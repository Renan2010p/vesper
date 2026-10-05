"""Gameplay system(s): DoorSystem."""

from __future__ import annotations

from ._base import *  # noqa: F401,F403
from ._base import _particles, _sfx


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
