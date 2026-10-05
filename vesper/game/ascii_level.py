"""Parse ASCII grids drawn with '#' into tile maps.

This is the format ``rooms.py`` uses.  A grid is either a list of rows
(``["####", "#..#"]``) or a newline-joined string; characters map to tiles and
a few letters are *markers* that spawn entities (ship, hatch, spawn point...).

Tiles
-----
``#`` wall      ``.`` / space floor      ``=`` one-way ledge
``^`` spikes    ``~`` lava               ``%`` breakable wall
``,`` moss/deco

Markers (the tile under them is left empty)
-------------------------------------------
``N`` gunship (a run of them sets its centre)
``|`` vertical hatch   ``-`` horizontal hatch   ``D`` single hatch
``@`` player spawn     ``S`` save station
``M`` missile  ``C`` charge beam  ``W`` drone form  ``G`` grav boots
``H`` dash     ``K`` mag grip      ``T`` energy tank  ``X`` missile tank
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterator, List, Optional, Tuple

from .config import (T_CRYSTAL, T_EMPTY, T_LAVA, T_MOSS, T_ONEWAY, T_SPIKE,
                     T_SURFACE)

TILE_BY_CHAR: Dict[str, int] = {
    "#": T_SURFACE,
    ".": T_EMPTY,
    " ": T_EMPTY,
    "=": T_ONEWAY,
    "^": T_SPIKE,
    "~": T_LAVA,
    "%": T_CRYSTAL,
    ",": T_MOSS,
    "|": T_EMPTY,   # hatch marker
    "-": T_EMPTY,   # hatch marker
    "D": T_EMPTY,   # hatch marker
    "N": T_EMPTY,   # ship marker
    "@": T_EMPTY,   # spawn marker
    "S": T_EMPTY,   # save marker
}

ITEM_BY_CHAR: Dict[str, str] = {
    "M": "missile", "C": "charge", "W": "morph", "G": "grav_boots",
    "H": "dash", "K": "wall_grip", "T": "energy_tank", "X": "missile_tank",
}

# item markers leave the tile empty (they only spawn a pickup)
for _ch in ITEM_BY_CHAR:
    TILE_BY_CHAR[_ch] = T_EMPTY


@dataclass
class AsciiMap:
    rows: List[str]
    source: str = ""

    @property
    def width(self) -> int:
        return len(self.rows[0]) if self.rows else 0

    @property
    def height(self) -> int:
        return len(self.rows)

    def char(self, col: int, row: int) -> str:
        if 0 <= row < self.height and 0 <= col < len(self.rows[row]):
            return self.rows[row][col]
        return " "

    def horizontal_runs(self, chars: str) -> Iterator[Tuple[str, int, int, int]]:
        for r, line in enumerate(self.rows):
            c = 0
            while c < len(line):
                if line[c] in chars:
                    ch = line[c]
                    c0 = c
                    while c < len(line) and line[c] == ch:
                        c += 1
                    yield ch, c0, r, c - c0
                else:
                    c += 1

    def vertical_runs(self, chars: str) -> Iterator[Tuple[str, int, int, int]]:
        for c in range(self.width):
            r = 0
            while r < self.height:
                ch = self.char(c, r)
                if ch in chars:
                    c0, r0 = c, r
                    while r < self.height and self.char(c, r) == ch:
                        r += 1
                    yield ch, c0, r0, r - r0
                else:
                    r += 1

    def first(self, target: str) -> Optional[Tuple[int, int]]:
        for r, line in enumerate(self.rows):
            c = line.find(target)
            if c >= 0:
                return c, r
        return None


def parse(grid, source: str = "") -> AsciiMap:
    """Normalise a grid (list of rows or one string) into an :class:`AsciiMap`."""
    lines = grid.splitlines() if isinstance(grid, str) else list(grid)
    lines = [ln.rstrip("\r\n\r") for ln in lines]
    while lines and not lines[-1].strip():
        lines.pop()
    width = max((len(ln) for ln in lines), default=0)
    lines = [ln.ljust(width) for ln in lines]
    return AsciiMap(lines, source)
