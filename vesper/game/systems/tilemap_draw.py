"""Gameplay system(s): TileMapDrawSystem, TileMapForegroundSystem."""

from __future__ import annotations

from ._base import *  # noqa: F401,F403


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
