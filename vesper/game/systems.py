"""Gameplay systems.

Each system owns one concern (control, AI, projectiles, damage, pickups...).
They communicate through the ECS and the event bus, never by calling each other,
so they can be reordered, replaced or extended independently.
"""

from __future__ import annotations

import math
import random
from typing import Optional

import pygame

from vesper.engine.ecs import System, World
from vesper.engine.physics import Body, Transform
from vesper.engine.render import Animator, Sprite

from . import art
from .components import (AI, Boss, ContactDamage, Door, Drops, Floating, Forms, Gate,
                         Health, Lifetime, Loadout, Pickup, Player, Projectile,
                         SaveStation, Ship, Spawner)
from .config import (AIR_ACCEL, CHARGE_TIME, COYOTE_TIME, DASH_COOLDOWN,
                     DASH_SPEED, DASH_TIME, DAMAGE_INVULN, GRAVITY,
                     GROUND_ACCEL, GROUND_FRICTION, JUMP_BUFFER, JUMP_CUT,
                     JUMP_SPEED, MAX_FALL, MORPH_SPEED, RUN_SPEED, WEAPON_TIER,
                     WALL_JUMP_X, WALL_JUMP_Y, WALL_SLIDE_SPEED)
from .items import apply_item
from .i18n import t
from .prefabs import spawn_enemy, spawn_pickup, spawn_projectile

# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _registry(world: World):
    return world.services["registry"]


def _audio(world: World):
    return world.services.get("audio")


def _particles(world: World):
    return world.services.get("particles")


def _sfx(world: World, name: str, volume: float = 1.0) -> None:
    audio = _audio(world)
    if audio:
        audio.play(name, volume)


def apply_damage(world: World, ent, amount: float, source: Optional[tuple] = None,
                 knockback: float = 0.0, ignore_invuln: bool = False) -> bool:
    health: Health = ent.get(Health)
    if health is None or health.dead:
        return False
    if health.invuln > 0 and not ignore_invuln:
        return False
    health.hp -= amount
    if not ignore_invuln:
        health.invuln = DAMAGE_INVULN
    health.flash = 0.14
    if ent.has_tag("player"):
        player: Player = ent.get(Player)
        if player:
            player.hurt_timer = 0.30
        body: Body = ent.get(Body)
        if body is not None and source is not None and knockback:
            direction = -1 if source[0] > ent.get(Transform).x else 1
            body.vx = direction * knockback
            body.vy = -knockback * 0.45
        _sfx(world, "player_hurt")
        particles = _particles(world)
        if particles:
            tr = ent.get(Transform)
            particles.burst(tr.x + tr.w / 2, tr.y + tr.h / 2, (255, 90, 110), 10, 160)
    if health.hp <= 0:
        health.hp = 0
        health.dead = True
    if world.events:
        world.events.emit("damaged", entity=ent, amount=amount)
    return True


# ---------------------------------------------------------------------------
# floating / bobbing
# ---------------------------------------------------------------------------

class FloatingSystem(System):
    priority = 5

    def update(self, world: World, dt: float) -> None:
        for ent in world.query(Transform, Floating):
            fl: Floating = ent.get(Floating)
            tr: Transform = ent.get(Transform)
            fl.phase += dt * fl.speed
            tr.y = fl.base_y + math.sin(fl.phase) * fl.amplitude


# ---------------------------------------------------------------------------
# gates
# ---------------------------------------------------------------------------

class GateSystem(System):
    priority = 14

    def update(self, world: World, dt: float) -> None:
        player = world.first(tag="player")
        loadout: Loadout | None = player.get(Loadout) if player else None
        for ent in world.query(Gate):
            gate: Gate = ent.get(Gate)
            if gate.open:
                continue
            unlocked = False
            if loadout is not None:
                if gate.required and loadout.has(gate.required):
                    unlocked = True
                if gate.cores_needed and loadout.cores >= gate.cores_needed:
                    unlocked = True
            if unlocked:
                gate.open = True
                tr = ent.get(Transform)
                _sfx(world, "door")
                particles = _particles(world)
                if particles:
                    particles.burst(tr.x + tr.w / 2, tr.y + tr.h / 2, (150, 240, 255), 26, 240)
                opened = world.services.get("gate_art", {}).get(ent.id)
                if opened is not None:
                    ent.get(Sprite).surface = opened
                if world.events:
                    world.events.emit("gate_opened", gate=gate)


# ---------------------------------------------------------------------------
# AI
# ---------------------------------------------------------------------------

class DoorSystem(System):
    """Shoot-to-open hatches.

    A door is solid until a projectile of a high enough tier (any beam <
    missile < super missile) hits it.  It stays open while the player is near
    and closes a moment after they leave.
    """

    priority = 16

    def update(self, world: World, dt: float) -> None:
        player = world.first(tag="player")
        prect = player.get(Transform).as_rect().inflate(10, 10) if player else None
        projectiles = list(world.query(Transform, Projectile))
        for ent in world.query(Transform, Door):
            door: Door = ent.get(Door)
            tr: Transform = ent.get(Transform)
            sprite: Sprite = ent.get(Sprite)
            rect = tr.as_rect()

            if not door.open:
                for proj_ent in projectiles:
                    proj: Projectile = proj_ent.get(Projectile)
                    if proj.team != "player":
                        continue
                    if not rect.colliderect(proj_ent.get(Transform).as_rect()):
                        continue
                    if proj.tier < door.tier:
                        continue
                    door.open = True
                    door.open_timer = 0.6
                    _sfx(world, "door")
                    particles = _particles(world)
                    if particles:
                        particles.burst(rect.centerx, rect.centery, (150, 240, 255), 14, 200)
                    if proj.pierce > 0:
                        proj.pierce -= 1
                    else:
                        lifetime = proj_ent.get(Lifetime)
                        if lifetime is not None:
                            lifetime.remaining = 0.0
                        proj_ent.destroy()
                    if world.events:
                        world.events.emit("door_opened")
                    break

            if door.open:
                door.anim = min(1.0, door.anim + dt * 4.0)
                if prect is not None and rect.colliderect(prect):
                    door.open_timer = max(door.open_timer, 0.4)
                else:
                    door.open_timer -= dt
                    if door.open_timer <= 0:
                        door.open = False
            else:
                door.anim = max(0.0, door.anim - dt * 4.0)

            frames = world.services.get("door_frames", {}).get(ent.id)
            if frames:
                index = int(round(door.anim * (len(frames) - 1)))
                sprite.surface = frames[min(len(frames) - 1, max(0, index))]


class AISystem(System):
    priority = 20

    def update(self, world: World, dt: float) -> None:
        registry = _registry(world)
        for ent in world.query(AI):
            if ent.has(Health) and ent.get(Health).dead:
                continue
            ai: AI = ent.get(AI)
            if not registry.has("ai", ai.behavior):
                continue
            registry.get("ai", ai.behavior)(world, ent, dt)


# ---------------------------------------------------------------------------
# player control
# ---------------------------------------------------------------------------

def _aim_vector(aim: str, facing: int) -> tuple:
    if aim == "up":
        return (0.0, -1.0)
    if aim == "down":
        return (0.0, 1.0)
    if aim == "updiag":
        return (facing * 0.7071, -0.7071)
    if aim == "downdiag":
        return (facing * 0.7071, 0.7071)
    return (float(facing), 0.0)


def _anim_aim(aim: str) -> str:
    if aim in ("up", "updiag"):
        return "up"
    if aim in ("down", "downdiag"):
        return "down"
    return "side"


def _blocked(world: World, rect: pygame.Rect) -> bool:
    service = world.services.get("collision")
    if service is None:
        return False
    for solid, oneway in service.solids(world, rect):
        if oneway:
            continue
        if rect.colliderect(solid):
            return True
    return False


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


def _approach(value: float, target: float, delta: float) -> float:
    if value < target:
        return min(value + delta, target)
    if value > target:
        return max(value - delta, target)
    return value


# ---------------------------------------------------------------------------
# projectiles
# ---------------------------------------------------------------------------

class ProjectileSystem(System):
    priority = 30

    def update(self, world: World, dt: float) -> None:
        tm = world.services.get("tilemap")
        for ent in list(world.query(Transform, Body, Projectile)):
            proj: Projectile = ent.get(Projectile)
            tr: Transform = ent.get(Transform)
            body: Body = ent.get(Body)
            lifetime: Lifetime = ent.get(Lifetime)

            if lifetime:
                lifetime.remaining -= dt
                if lifetime.remaining <= 0:
                    ent.destroy()
                    continue

            # gravity + homing
            if proj.gravity:
                body.vy += proj.gravity * dt
            if proj.homing:
                target = self._find_target(world, tr, proj.team)
                if target is not None:
                    tt: Transform = target.get(Transform)
                    dx = tt.x + tt.w / 2 - (tr.x + tr.w / 2)
                    dy = tt.y + tt.h / 2 - (tr.y + tr.h / 2)
                    d = math.hypot(dx, dy) or 1.0
                    speed = math.hypot(body.vx, body.vy)
                    body.vx += (dx / d) * speed * proj.homing * dt
                    body.vy += (dy / d) * speed * proj.homing * dt

            rect = tr.as_rect()

            # -- breakable / solid tiles ------------------------------------
            if tm is not None and self._hit_tiles(world, tm, ent, tr, proj):
                continue

            # -- entities ---------------------------------------------------
            hit = False
            for other in world.query(Transform, Health):
                if other.id == proj.owner:
                    continue
                oh: Health = other.get(Health)
                if oh.team == proj.team or oh.dead:
                    continue
                otr: Transform = other.get(Transform)
                if not rect.colliderect(otr.as_rect()):
                    continue
                self._damage(world, ent, proj, other, otr)
                if proj.pierce > 0:
                    proj.pierce -= 1
                    continue
                hit = True
                break
            if hit:
                ent.destroy()

    def _find_target(self, world: World, tr: Transform, team: str):
        best = None
        best_d = 1e9
        for other in world.query(Transform, Health):
            oh: Health = other.get(Health)
            if oh.team == team or oh.dead:
                continue
            otr: Transform = other.get(Transform)
            d = (otr.x - tr.x) ** 2 + (otr.y - tr.y) ** 2
            if d < best_d:
                best_d = d
                best = other
        return best

    def _hit_tiles(self, world, tm, ent, tr: Transform, proj: Projectile) -> bool:
        cx, cy = tr.x + tr.w / 2, tr.y + tr.h / 2
        ts = tm.tile_size
        tx, ty = int(cx // ts), int(cy // ts)
        if not tm.in_bounds(tx, ty):
            return False
        definition = tm.get_def(tx, ty)
        if definition.breakable and proj.breaks_tiles:
            radius = max(0, proj.break_radius)
            for oy in range(ty - radius, ty + radius + 1):
                for ox in range(tx - radius, tx + radius + 1):
                    if tm.get_def(ox, oy).breakable:
                        tm.set(ox, oy, 0)
            particles = _particles(world)
            if particles:
                particles.burst(tx * ts + ts / 2, ty * ts + ts / 2, (255, 190, 120), 16, 200)
            _sfx(world, "explode", 0.6)
            if world.events:
                world.events.emit("tile_broken", tx=tx, ty=ty)
            ent.destroy()
            return True
        if definition.solid and not definition.oneway:
            particles = _particles(world)
            if particles:
                particles.spawn(cx, cy, count=5, color=(180, 240, 255), speed=120,
                                life=0.2, radius=1.5)
            ent.destroy()
            return True
        return False

    def _damage(self, world, ent, proj: Projectile, other, otr: Transform) -> None:
        apply_damage(world, other, proj.damage,
                     source=(ent.get(Transform).x, ent.get(Transform).y),
                     knockback=proj.knockback)
        particles = _particles(world)
        if particles:
            particles.spawn(otr.x + otr.w / 2, otr.y + otr.h / 2, count=6,
                            color=(255, 220, 160), speed=150, life=0.25, radius=2)
        _sfx(world, "enemy_hit")


# ---------------------------------------------------------------------------
# hazards & contact
# ---------------------------------------------------------------------------

class HazardSystem(System):
    priority = 60

    def update(self, world: World, dt: float) -> None:
        tm = world.services.get("tilemap")
        player = world.first(tag="player")
        if player is None:
            return
        phealth: Health = player.get(Health)
        if phealth.dead:
            return
        ptr: Transform = player.get(Transform)

        # tile hazards (continuous, ignores i-frames)
        if tm is not None:
            total = 0.0
            for tx, ty in tm.tiles_overlapping(ptr.x + 2, ptr.y + 2, ptr.w - 4, ptr.h - 4):
                total += tm.hazard_damage(tx, ty)
            if total > 0:
                apply_damage(world, player, total * dt, ignore_invuln=True)
                player.get(Health).invuln = max(player.get(Health).invuln, 0.35)

        # contact damage
        if phealth.invuln <= 0:
            prect = ptr.as_rect()
            for enemy in world.query(Transform, ContactDamage):
                ehealth: Health = enemy.get(Health)
                if ehealth.dead:
                    continue
                etr: Transform = enemy.get(Transform)
                if prect.colliderect(etr.as_rect()):
                    contact: ContactDamage = enemy.get(ContactDamage)
                    apply_damage(world, player, contact.damage,
                                 source=(etr.x, etr.y), knockback=contact.recoil)
                    break


# ---------------------------------------------------------------------------
# status effects / invuln / flash
# ---------------------------------------------------------------------------

class StatusSystem(System):
    priority = 55

    def update(self, world: World, dt: float) -> None:
        for ent in world.query(Health):
            health: Health = ent.get(Health)
            if health.invuln > 0:
                health.invuln -= dt
            if health.flash > 0:
                health.flash -= dt
            sprite: Sprite | None = ent.get(Sprite)
            if sprite is not None:
                if ent.has_tag("player") and health.invuln > 0:
                    sprite.alpha = 110 if int(health.invuln * 20) % 2 == 0 else 255
                elif health.flash > 0:
                    sprite.alpha = 150
                else:
                    sprite.alpha = 255


# ---------------------------------------------------------------------------
# pickups
# ---------------------------------------------------------------------------

class PickupSystem(System):
    priority = 70

    def update(self, world: World, dt: float) -> None:
        player = world.first(tag="player")
        if player is None:
            return
        prect = player.get(Transform).as_rect()
        for ent in list(world.query(Transform, Pickup)):
            pickup: Pickup = ent.get(Pickup)
            if pickup.taken:
                continue
            if not prect.colliderect(ent.get(Transform).as_rect()):
                continue
            pickup.taken = True
            item = apply_item(world, player, pickup.item_id)
            tr = ent.get(Transform)
            is_ability = item.kind == "ability"
            _sfx(world, "upgrade" if is_ability else "pickup")
            particles = _particles(world)
            if particles:
                particles.burst(tr.x + tr.w / 2, tr.y + tr.h / 2,
                                art.ITEM_COLORS.get(pickup.item_id, (255, 255, 255)), 22, 240)
            if world.events:
                world.events.emit("toast", title=t(item.name), subtitle=t(item.subtitle),
                                  kind=item.kind)
            ent.destroy()


# ---------------------------------------------------------------------------
# save stations
# ---------------------------------------------------------------------------

class SaveStationSystem(System):
    priority = 70

    def update(self, world: World, dt: float) -> None:
        player = world.first(tag="player")
        if player is None:
            return
        prect = player.get(Transform).as_rect().inflate(4, 4)
        for ent in world.query(Transform, SaveStation):
            station: SaveStation = ent.get(SaveStation)
            if not prect.colliderect(ent.get(Transform).as_rect()):
                station.used = False
                continue
            if station.used:
                continue
            station.used = True
            callback = world.services.get("save_callback")
            if callback:
                callback(player)
            _sfx(world, "save")
            if world.events:
                world.events.emit("toast", title=t("toast.saved"),
                                  subtitle=t("toast.saved_sub"), kind="save")


# ---------------------------------------------------------------------------
# gunship (board to refuel / save)
# ---------------------------------------------------------------------------

class ShipSystem(System):
    priority = 72

    def update(self, world: World, dt: float) -> None:
        world.services["ship_nearby"] = False
        player = world.first(tag="player")
        if player is None:
            return
        prect = player.get(Transform).as_rect()
        for ent in world.query(Transform, Ship):
            ship: Ship = ent.get(Ship)
            tr: Transform = ent.get(Transform)
            cx = tr.x + tr.w / 2
            bottom = tr.y + tr.h
            entrance = pygame.Rect(int(cx - ship.entrance_w / 2),
                                   int(bottom - ship.entrance_h),
                                   int(ship.entrance_w), int(ship.entrance_h))
            if prect.colliderect(entrance):
                world.services["ship_nearby"] = True
                break


# ---------------------------------------------------------------------------
# spawners
# ---------------------------------------------------------------------------

class SpawnerSystem(System):
    priority = 18

    def update(self, world: World, dt: float) -> None:
        player = world.first(tag="player")
        if player is None:
            return
        p_tr = player.get(Transform)
        for ent in world.query(Transform, Spawner):
            sp: Spawner = ent.get(Spawner)
            if not sp.active:
                continue
            tr = ent.get(Transform)
            if math.hypot(p_tr.x - tr.x, p_tr.y - tr.y) > 340:
                continue
            sp.timer -= dt
            if sp.timer > 0:
                continue
            sp.timer = sp.interval
            nearby = 0
            for other in world.query(Health, tag="enemy"):
                otr = other.get(Transform)
                if math.hypot(otr.x - tr.x, otr.y - tr.y) < sp.radius:
                    nearby += 1
            if nearby < sp.cap:
                spawn_enemy(world, sp.prefab, tr.x + random.uniform(-20, 20), tr.y)


# ---------------------------------------------------------------------------
# death & drops
# ---------------------------------------------------------------------------

class DeathSystem(System):
    priority = 80

    def update(self, world: World, dt: float) -> None:
        for ent in list(world.query(Health)):
            health: Health = ent.get(Health)
            if not health.dead:
                continue
            tr = ent.get(Transform)
            if ent.has_tag("player"):
                if world.events:
                    world.events.emit("player_died")
                health.dead = False  # scene decides; avoid repeat emits each frame
                continue
            # enemy death
            is_boss = ent.has_tag("boss")
            particles = _particles(world)
            if particles:
                particles.burst(tr.x + tr.w / 2, tr.y + tr.h / 2,
                                (255, 160, 90), 40 if is_boss else 16,
                                420 if is_boss else 240)
            _sfx(world, "explode" if is_boss else "enemy_die")
            drops: Drops | None = ent.get(Drops)
            if drops and drops.items and random.random() < drops.chance:
                item_id = random.choice(drops.items)
                spawn_pickup(world, item_id, tr.x + tr.w / 2, tr.y + tr.h / 2)
            if is_boss and world.events:
                world.events.emit("boss_defeated")
            world.services["kill_count"] = world.services.get("kill_count", 0) + 1
            world.services.get("enemy_defs", {}).pop(ent.id, None)
            ent.destroy()


# ---------------------------------------------------------------------------
# camera
# ---------------------------------------------------------------------------

class CameraSystem(System):
    priority = 40

    def update(self, world: World, dt: float) -> None:
        camera = world.services.get("camera")
        player = world.first(tag="player")
        if camera is None or player is None:
            return
        tr: Transform = player.get(Transform)
        player_comp: Player | None = player.get(Player)
        lookahead = 40.0 * (player_comp.facing if player_comp else 1)
        camera.follow(tr.x + tr.w / 2, tr.y + tr.h / 2, dt, lookahead)
        camera.update(dt)


# ---------------------------------------------------------------------------
# tile map drawing
# ---------------------------------------------------------------------------

class TileMapDrawSystem(System):
    priority = 800

    def __init__(self, foreground: bool = False) -> None:
        self.foreground = foreground
        self.surfaces = {}
        self._tileset = None

    def _ensure_surfaces(self, tm) -> None:
        # rebuild when the room (and thus the tileset reference) changes
        if tm is not None and tm.tileset is not self._tileset:
            self.surfaces = art.build_tile_surfaces(tm.tileset, tm.tile_size)
            self._tileset = tm.tileset

    def start(self, world: World) -> None:
        self._ensure_surfaces(world.services.get("tilemap"))

    def draw(self, world: World, surface, camera) -> None:
        tm = world.services.get("tilemap")
        if tm is None:
            return
        self._ensure_surfaces(tm)
        view = camera.view_rect()
        ts = tm.tile_size
        ox, oy = camera.offset
        defs = tm.tileset
        x0 = max(0, view.left // ts)
        y0 = max(0, view.top // ts)
        x1 = min(tm.width - 1, view.right // ts)
        y1 = min(tm.height - 1, view.bottom // ts)
        for ty in range(y0, y1 + 1):
            for tx in range(x0, x1 + 1):
                tile_id = tm.get(tx, ty)
                if tile_id == 0:
                    continue
                definition = defs[tile_id]
                if definition.foreground != self.foreground:
                    continue
                surf = self.surfaces.get(tile_id)
                if surf is None:
                    continue
                surface.blit(surf, (tx * ts + ox, ty * ts + oy))


class TileMapForegroundSystem(TileMapDrawSystem):
    priority = 950

    def __init__(self) -> None:
        super().__init__(foreground=True)
