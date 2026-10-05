"""Tile based worlds.

The tile map is deliberately dumb: a grid of integer ids plus a table of
:class:`TileDef`.  Solid/hazard/breakable behaviour comes from the table, so
new tile kinds are added by registering a definition -- no code changes.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterator, List, Tuple

EMPTY = 0
OUT_OF_BOUNDS = -1


@dataclass
class TileDef:
    name: str
    solid: bool = False
    #: contact damage per second (0 = harmless)
    hazard: int = 0
    breakable: bool = False
    #: one-way platforms only collide when falling onto them
    oneway: bool = False
    #: foreground tiles are drawn over entities, background behind
    foreground: bool = False
    #: arbitrary gameplay tags a system may look up ("ice","lava","climb")
    tags: Tuple[str, ...] = ()
    color: Tuple[int, int, int] = (90, 90, 110)
    color2: Tuple[int, int, int] = (60, 60, 80)


class TileSet:
    def __init__(self) -> None:
        self._defs: Dict[int, TileDef] = {}
        self.add(EMPTY, TileDef("empty", solid=False, color=(0, 0, 0)))

    def add(self, tile_id: int, definition: TileDef) -> TileDef:
        self._defs[tile_id] = definition
        return definition

    def __getitem__(self, tile_id: int) -> TileDef:
        try:
            return self._defs[tile_id]
        except KeyError:
            return self._defs[EMPTY]

    def __contains__(self, tile_id: int) -> bool:
        return tile_id in self._defs

    def defs(self):
        return dict(self._defs)


class TileMap:
    def __init__(self, width: int, height: int, tile_size: int, tileset: TileSet,
                 fill: int = EMPTY) -> None:
        self.width = width
        self.height = height
        self.tile_size = tile_size
        self.tileset = tileset
        self.grid: List[List[int]] = [[fill for _ in range(width)] for _ in range(height)]

    # -- coordinate helpers ----------------------------------------------
    @property
    def pixel_width(self) -> int:
        return self.width * self.tile_size

    @property
    def pixel_height(self) -> int:
        return self.height * self.tile_size

    def in_bounds(self, tx: int, ty: int) -> bool:
        return 0 <= tx < self.width and 0 <= ty < self.height

    def get(self, tx: int, ty: int) -> int:
        if not self.in_bounds(tx, ty):
            return OUT_OF_BOUNDS
        return self.grid[ty][tx]

    def get_def(self, tx: int, ty: int) -> TileDef:
        return self.tileset[self.get(tx, ty)]

    def set(self, tx: int, ty: int, tile_id: int) -> None:
        if self.in_bounds(tx, ty):
            self.grid[ty][tx] = tile_id

    # -- queries ----------------------------------------------------------
    def is_solid(self, tx: int, ty: int) -> bool:
        tile = self.get(tx, ty)
        if tile == OUT_OF_BOUNDS:
            return True  # treat outside the map as solid
        return self.tileset[tile].solid

    def hazard_damage(self, tx: int, ty: int) -> int:
        return self.tileset[self.get(tx, ty)].hazard

    def try_break(self, tx: int, ty: int, power: int = 1) -> bool:
        """Break a breakable tile.  Returns True if the tile was removed."""
        definition = self.get_def(tx, ty)
        if definition.breakable:
            self.set(tx, ty, EMPTY)
            return True
        return False

    # -- iteration --------------------------------------------------------
    def tiles_overlapping(self, x: float, y: float, w: float, h: float) -> Iterator[Tuple[int, int]]:
        ts = self.tile_size
        x0 = int(x // ts)
        y0 = int(y // ts)
        x1 = int((x + w - 1) // ts)
        y1 = int((y + h - 1) // ts)
        for ty in range(y0, y1 + 1):
            for tx in range(x0, x1 + 1):
                yield tx, ty
