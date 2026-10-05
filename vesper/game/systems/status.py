"""Gameplay system(s): StatusSystem."""

from __future__ import annotations

from ._base import *  # noqa: F401,F403


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
