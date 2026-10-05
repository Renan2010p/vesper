"""Gameplay system(s): SaveStationSystem."""

from __future__ import annotations

from ._base import *  # noqa: F401,F403
from ._base import _sfx


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
