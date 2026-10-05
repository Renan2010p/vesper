"""Gameplay system(s): CameraSystem."""

from __future__ import annotations

from ._base import *  # noqa: F401,F403


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
