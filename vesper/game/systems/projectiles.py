"""Gameplay system(s): ProjectileSystem."""

from __future__ import annotations

from ._base import *  # noqa: F401,F403
from ._base import _particles, _sfx, apply_damage


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
