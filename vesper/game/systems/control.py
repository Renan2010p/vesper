"""Gameplay system(s): PlayerControlSystem."""

from __future__ import annotations

from ._base import *  # noqa: F401,F403
from ._base import _approach, _aim_vector, _anim_aim, _blocked, _particles, _registry, _sfx


class PlayerControlSystem(System):
    priority = 20

    def update(self, world: World, dt: float) -> None:
        inp = world.services["input"]
        player_ent = world.first(tag="player")
        if player_ent is None:
            return
        health: Health = player_ent.get(Health)
        if health.dead:
            return

        tr: Transform = player_ent.get(Transform)
        body: Body = player_ent.get(Body)
        player: Player = player_ent.get(Player)
        loadout: Loadout = player_ent.get(Loadout)
        sprite: Sprite = player_ent.get(Sprite)
        animator: Animator = player_ent.get(Animator)
        forms: Forms = player_ent.get(Forms)

        # -- timers ---------------------------------------------------------
        player.fire_cd = max(0.0, player.fire_cd - dt)
        player.dash_cd = max(0.0, player.dash_cd - dt)
        player.morph_lock = max(0.0, player.morph_lock - dt)
        player.hurt_timer = max(0.0, player.hurt_timer - dt)
        player.land_timer = max(0.0, player.land_timer - dt)

        # landing squash: just touched the ground
        if body.on_ground and not player.was_ground:
            player.land_timer = 0.12
        player.was_ground = body.on_ground

        if body.on_ground:
            player.coyote = COYOTE_TIME
        else:
            player.coyote = max(0.0, player.coyote - dt)

        # -- morph form -----------------------------------------------------
        if loadout.has("morph"):
            self._update_morph(world, player_ent, tr, body, player, loadout,
                               sprite, animator, forms, inp, dt)

        # -- aim ------------------------------------------------------------
        moving = abs(inp.axis()) > 0.1
        if not player.morph:
            if inp.held("up") and moving:
                player.aim = "updiag"
            elif inp.held("down") and not body.on_ground:
                player.aim = "downdiag"
            elif inp.held("up"):
                player.aim = "up"
            elif inp.held("down"):
                player.aim = "down"
            else:
                player.aim = "side"

        # -- dash -----------------------------------------------------------
        if player.dash_timer > 0:
            player.dash_timer -= dt
            body.gravity = player.dash_timer <= 0
            body.vx = DASH_SPEED * player.dash_dir
            body.vy = 0.0
            health.invuln = max(health.invuln, 0.05)
        elif inp.pressed("dash") and loadout.has("dash") and player.dash_cd <= 0 \
                and not player.morph:
            player.dash_timer = DASH_TIME
            player.dash_cd = DASH_COOLDOWN
            player.dash_dir = player.facing
            body.gravity = False
            _sfx(world, "dash")
            particles = _particles(world)
            if particles:
                particles.burst(tr.x + tr.w / 2, tr.y + tr.h / 2, (255, 140, 200), 14, 200)

        # -- horizontal movement -------------------------------------------
        if player.dash_timer <= 0:
            axis = 0.0 if player.morph else inp.axis()
            speed = MORPH_SPEED if player.morph else RUN_SPEED
            target = axis * speed
            if axis != 0:
                accel = GROUND_ACCEL if body.on_ground else AIR_ACCEL
                if player.morph:
                    accel *= 0.7
                body.vx = _approach(body.vx, target, accel * dt)
                if not player.morph:
                    player.facing = 1 if axis > 0 else -1
            else:
                if body.on_ground:
                    body.vx = _approach(body.vx, 0, GROUND_FRICTION * dt)
                else:
                    body.vx = _approach(body.vx, 0, AIR_ACCEL * 0.3 * dt)

        # -- wall sliding ---------------------------------------------------
        wall_dir = 0
        if body.on_wall_left:
            wall_dir = -1
        elif body.on_wall_right:
            wall_dir = 1
        player.wall_sliding = False
        if not body.on_ground and wall_dir != 0 and body.vy > 0 \
                and inp.axis() == wall_dir:
            player.wall_sliding = True
            body.vy = min(body.vy, WALL_SLIDE_SPEED)

        # -- jumping --------------------------------------------------------
        if inp.pressed("jump"):
            player.jump_buffer = JUMP_BUFFER
        else:
            player.jump_buffer = max(0.0, player.jump_buffer - dt)

        max_jumps = 2 if loadout.has("grav_boots") else 1
        if body.on_ground or player.wall_sliding:
            player.jumps_left = max_jumps

        if player.jump_buffer > 0 and not player.morph:
            if body.on_ground or player.coyote > 0:
                self._jump(player_ent, body, player)
            elif wall_dir != 0 and not body.on_ground:
                # wall jump: always available, like the classic wall kick
                self._wall_jump(player, body, wall_dir)
            elif player.jumps_left > 0 and not body.on_ground and player.coyote <= 0 \
                    and loadout.has("grav_boots"):
                player.jumps_left -= 1
                self._jump(player_ent, body, player, air=True)

        # variable jump height
        if inp.released("jump") and body.vy < 0 and player.dash_timer <= 0:
            body.vy *= JUMP_CUT

        # -- weapons --------------------------------------------------------
        if not player.morph:
            self._update_weapons(world, player_ent, player, loadout, inp, dt)

        # -- animation ------------------------------------------------------
        move_axis = 0.0 if player.morph else inp.axis()
        skidding = (body.on_ground and not player.morph and abs(body.vx) > 40
                    and move_axis != 0 and (move_axis > 0) != (body.vx > 0))
        self._update_animation(player_ent, body, player, sprite, animator, loadout,
                               skidding)

    # -- helpers ----------------------------------------------------------
    def _jump(self, ent, body: Body, player: Player, air: bool = False) -> None:
        body.vy = -JUMP_SPEED * (0.92 if air else 1.0)
        player.jump_buffer = 0.0
        player.coyote = 0.0
        if not air:
            player.jumps_left = max(0, player.jumps_left - 1) if player.jumps_left else 0

    def _wall_jump(self, player: Player, body: Body, wall_dir: int) -> None:
        body.vy = -WALL_JUMP_Y
        body.vx = -wall_dir * WALL_JUMP_X
        player.facing = -wall_dir
        player.jump_buffer = 0.0
        player.jumps_left = 1

    def _update_morph(self, world, ent, tr, body, player, loadout, sprite,
                      animator, forms, inp, dt) -> None:
        if not player.morph:
            if inp.held("down") and body.on_ground and abs(body.vx) < 40 and player.dash_timer <= 0:
                self._set_form(ent, tr, sprite, animator, forms, True)
                player.morph = True
                player.morph_lock = 0.15
                _sfx(world, "hit")
        else:
            if inp.pressed("jump") or inp.held("up"):
                # try to stand up: need headroom
                new_rect = pygame.Rect(round(tr.x), round(tr.y - (forms.human_size[1] - tr.h)),
                                       int(forms.human_size[0]), int(forms.human_size[1]))
                if not _blocked(world, new_rect):
                    self._set_form(ent, tr, sprite, animator, forms, False)
                    player.morph = False
                    player.morph_lock = 0.15
                    _sfx(world, "jump")

    def _set_form(self, ent, tr, sprite, animator, forms: Forms, morph: bool) -> None:
        if morph:
            new_h = forms.morph_size[1]
            tr.y += tr.h - new_h
            tr.w, tr.h = forms.morph_size
            sprite.offset = ((16 - tr.w) / 2, (16 - tr.h) / 2)
            animator.animations = forms.morph_anims
            animator.play("morph", restart=True)
        else:
            new_h = forms.human_size[1]
            tr.y -= new_h - tr.h
            tr.w, tr.h = forms.human_size
            sprite.offset = ((18 - tr.w) / 2, (24 - tr.h) / 2)
            animator.animations = forms.human_anims
            animator.play("idle_side", restart=True)

    def _update_weapons(self, world, ent, player: Player, loadout: Loadout, inp, dt) -> None:
        has_charge = loadout.has("charge")
        if has_charge and inp.held("fire"):
            player.charging = True
            player.charge = min(CHARGE_TIME, player.charge + dt)
        if inp.pressed("fire"):
            player.charging = True
            player.charge = 0.0
            if not has_charge and player.fire_cd <= 0:
                self._fire(world, ent, loadout, "beam")
        if inp.released("fire") and player.charging:
            player.charging = False
            if has_charge and player.fire_cd <= 0:
                if player.charge >= CHARGE_TIME:
                    self._fire(world, ent, loadout, "charged")
                else:
                    self._fire(world, ent, loadout, "beam")
            player.charge = 0.0
        # missiles
        if inp.pressed("ability") and loadout.has("missile") and player.fire_cd <= 0:
            if loadout.has("super_missile") and inp.held("up"):
                self._fire(world, ent, loadout, "super_missile")
            else:
                self._fire(world, ent, loadout, "missile")

    def _fire(self, world, ent, loadout: Loadout, weapon_id: str) -> bool:
        registry = _registry(world)
        weapon = registry.get("weapon", weapon_id)
        if weapon.ammo_cost:
            if loadout.missiles < weapon.ammo_cost:
                _sfx(world, "hit", 0.4)
                return False
            loadout.missiles -= weapon.ammo_cost
        tr: Transform = ent.get(Transform)
        player: Player = ent.get(Player)
        mx, my = _aim_vector(player.aim, player.facing)
        cx, cy = tr.x + tr.w / 2, tr.y + tr.h / 2
        spawn_projectile(world, weapon.projectile, cx + mx * 14, cy + my * 10,
                         mx * weapon.speed, my * weapon.speed, weapon.damage,
                         team="player", owner=ent.id, breaks_tiles=weapon.breaks_tiles,
                         break_radius=weapon.break_radius,
                         tier=WEAPON_TIER.get(weapon_id, 0))
        _sfx(world, weapon.sfx)
        particles = _particles(world)
        if particles:
            particles.spawn(cx + mx * 16, cy + my * 10, count=4, color=(150, 240, 255),
                            speed=90, life=0.2, radius=1.5,
                            angle=math.atan2(my, mx), spread=0.5)
        if world.events:
            world.events.emit("player_fired", weapon=weapon_id)
        player.fire_cd = max(player.fire_cd, weapon.cooldown)
        return True

    def _update_animation(self, ent, body, player, sprite, animator, loadout,
                          skidding: bool = False) -> None:
        if player.hurt_timer > 0:
            animator.play("hurt")
        elif player.dash_timer > 0:
            animator.play("dash")
        elif player.morph:
            animator.play("morph")
        elif player.land_timer > 0:
            animator.play("land")
        elif skidding:
            animator.play("skid")
        else:
            aim = _anim_aim(player.aim)
            if not body.on_ground:
                name = "spin"
            elif abs(body.vx) > 12:
                name = f"run_{aim}"
            else:
                name = f"idle_{aim}"
            animator.play(name)
        if not player.morph:
            sprite.flip_x = player.facing < 0
        else:
            sprite.flip_x = False
