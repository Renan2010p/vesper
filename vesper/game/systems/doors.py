"""Gameplay system(s): DoorSystem."""

from __future__ import annotations

from ._base import *  # noqa: F401,F403
from ._base import _particles, _sfx


class DoorSystem(System):
    """Sensor / shootable hatches.

    A plain hatch (tier 0) opens when the player touches it or when it is shot;
    an armoured hatch (missile / super) must be shot with the right weapon.  A
    hatch opened by touch closes shortly after the player steps away; one opened
    from a distance stays open until the player reaches it.
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
            # projectiles stop against the solid hatch, so test a small margin
            strike = rect.inflate(10, 10)

            if not door.open:
                if touching and door.tier == 0:
                    self._open(world, door, rect)
                    door.sensed = True
                else:
                    for proj_ent in projectiles:
                        proj: Projectile = proj_ent.get(Projectile)
                        if proj.team != "player":
                            continue
                        if not strike.colliderect(proj_ent.get(Transform).as_rect()):
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
                    door.sensed = True
                    door.open_timer = 0.5
                elif door.sensed:
                    door.open_timer -= dt
                    if door.open_timer <= 0:
                        door.open = False
                        door.sensed = False
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
