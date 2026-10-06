"""Gameplay system(s): ShipSystem."""

from __future__ import annotations

from ._base import *  # noqa: F401,F403


class ShipSystem(System):
    priority = 72

    def update(self, world: World, dt: float) -> None:
        world.services["ship_nearby"] = False

        # gentle hover (visual only -- collision still uses the transform)
        for ent in world.query(Transform, Ship, Sprite):
            ship: Ship = ent.get(Ship)
            if ship.hover:
                ship.phase += dt
                ent.get(Sprite).offset = (0.0, math.sin(ship.phase * 1.8) * 2.5)

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
