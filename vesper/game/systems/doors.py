"""Gameplay system(s): DoorSystem."""

from __future__ import annotations

from ._base import *  # noqa: F401,F403
from ._base import _particles, _sfx


class DoorSystem(System):
    """Sensor hatches.

    The basic hatch (tier 0) opens when the player touches it and closes a
    moment after they step away.  Armoured hatches (missile / super) still have
    to be shot with a weapon of the matching tier.
    """

    priority = 16

    def update(self, world: World, dt: float) -> None:
        player = world.first(tag="player")
        prect = player.get(Transform).as_rect().inflate(6, 6) if player else None
        projectiles = list(world.query(Transform, Projectile))
        for ent in world.query(Transform, Door):
            door: Door = ent.get(Door)
            tr: Transform = ent.get(Transform)
            sprite: Sprite = ent.get(Sprite)
            rect = tr.as_rect()
            touching = prect is not None and rect.colliderect(prect)

            if not door.open:
                if touching and door.tier == 0:
                    # a plain hatch senses the player and slides open
                    self._open(world, door, rect)
                else:
                    # armoured hatches must be shot with the right weapon
                    for proj_ent in projectiles:
                        proj: Projectile = proj_ent.get(Projectile)
                        if proj.team != "player":
                            continue
                        if not rect.colliderect(proj_ent.get(Transform).as_rect()):
                            continue
                        if proj.tier < door.tier:
                            continue
                        self._open(world, door, rect)
                        if proj.pierce > 0:
                            proj.pierce -= 1
                        else:
                            lifetime = proj_ent.get(Lifetime)
                            if lifetime is not None:
                                lifetime.remaining = 0.0
                            proj_ent.destroy()
                        break

            if door.open:
                door.anim = min(1.0, door.anim + dt * 4.0)
                if touching:
                    door.open_timer = max(door.open_timer, 0.5)
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

    def _open(self, world: World, door: Door, rect) -> None:
        door.open = True
        door.open_timer = 0.5
        _sfx(world, "door")
        particles = _particles(world)
        if particles:
            particles.burst(rect.centerx, rect.centery, (150, 240, 255), 14, 200)
        if world.events:
            world.events.emit("door_opened")
