"""Tileset and level data.

The world is now made of independent rooms (see ``rooms.py`` / ``roomworld.py``);
this module keeps the tileset and a small compatibility builder used by the
tools and tests.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Tuple

import pygame

from vesper.engine.tilemap import TileDef, TileMap, TileSet

from .config import T_BOSS_ARMOR, T_CRYSTAL, T_GRATE, T_ICE, T_LAVA, T_METAL, T_MOSS, T_ONEWAY, T_ROCK, T_ROCK_DARK, T_ROCK_FG, T_RUIN, T_SPIKE, T_SURFACE, T_SURFACE_TOP, T_VINE, ZONE_COLORS


def build_tileset() -> TileSet:
    ts = TileSet()
    ts.add(T_ROCK, TileDef("rock", solid=True, color=(72, 76, 98), color2=(48, 52, 72)))
    ts.add(T_ROCK_DARK, TileDef("rock_dark", solid=True, color=(50, 52, 72),
                                color2=(34, 36, 52)))
    ts.add(T_METAL, TileDef("metal", solid=True, color=(104, 112, 138),
                            color2=(70, 76, 100)))
    ts.add(T_ICE, TileDef("ice", solid=True, color=(126, 194, 226),
                          color2=(84, 146, 188), tags=("ice",)))
    ts.add(T_SPIKE, TileDef("spike", solid=False, hazard=45,
                            color=(214, 222, 236), color2=(130, 140, 160)))
    ts.add(T_LAVA, TileDef("lava", solid=False, hazard=80,
                           color=(224, 92, 40), color2=(255, 200, 90), tags=("lava",)))
    ts.add(T_CRYSTAL, TileDef("crystal", solid=True, breakable=True,
                              color=(168, 116, 62), color2=(104, 68, 30),
                              tags=("breakable",)))
    ts.add(T_ROCK_FG, TileDef("rock_fg", solid=False, foreground=True,
                              color=(18, 20, 32), color2=(8, 8, 16)))
    ts.add(T_ONEWAY, TileDef("oneway", solid=True, oneway=True,
                             color=(124, 112, 92), color2=(84, 74, 60)))
    ts.add(T_VINE, TileDef("vine", solid=False, color=(40, 92, 60),
                           color2=(24, 60, 40)))
    ts.add(T_GRATE, TileDef("grate", solid=False, color=(46, 50, 70),
                            color2=(28, 30, 44)))
    ts.add(T_BOSS_ARMOR, TileDef("boss_armor", solid=True, color=(94, 82, 116),
                                 color2=(62, 54, 84)))
    ts.add(T_SURFACE, TileDef("surface", solid=True, color=(88, 76, 64),
                              color2=(60, 52, 44), tags=("surface",)))
    ts.add(T_RUIN, TileDef("ruin", solid=True, color=(152, 148, 140),
                           color2=(104, 100, 94), tags=("ruin",)))
    ts.add(T_MOSS, TileDef("moss", solid=False, color=(58, 112, 84),
                           color2=(34, 74, 56), tags=("moss",)))
    ts.add(T_SURFACE_TOP, TileDef("surface_top", solid=True, color=(88, 76, 64),
                                  color2=(58, 50, 42), tags=("surface",)))
    return ts


@dataclass
class Zone:
    name: str
    rect: pygame.Rect
    colors: Tuple[Tuple[int, int, int], Tuple[int, int, int]]


@dataclass
class LevelData:
    tileset: TileSet
    tilemap: TileMap
    zones: List[Zone]
    player_spawn: Tuple[float, float]
    enemies: List[Tuple[str, float, float]] = field(default_factory=list)
    pickups: List[Tuple[str, float, float]] = field(default_factory=list)
    gates: List[dict] = field(default_factory=list)
    doors: List[dict] = field(default_factory=list)
    saves: List[Tuple[float, float]] = field(default_factory=list)
    spawners: List[dict] = field(default_factory=list)
    landing_pad: Tuple[float, float] = (0.0, 0.0)
    decorations: List[tuple] = field(default_factory=list)
    rooms: List[dict] = field(default_factory=list)

    def zone_at(self, px: float, py: float) -> Zone:
        for zone in self.zones:
            if zone.rect.collidepoint(px, py):
                return zone
        return self.zones[0]


def build_level() -> LevelData:
    """Compatibility: the starting room as a LevelData (used by tools/tests)."""
    from .roomworld import build_room
    from .rooms import START_ROOM

    ts = build_tileset()
    room = build_room(START_ROOM, ts)
    tm = room.tilemap
    rect = pygame.Rect(0, 0, tm.pixel_width, tm.pixel_height)
    zones = [Zone(room.zone, rect, ZONE_COLORS.get(room.zone, ZONE_COLORS["unknown"]))]
    rooms = [{"name": room.id, "label": room.label, "x": 0, "y": 0,
              "w": tm.width, "h": tm.height}]
    return LevelData(ts, tm, zones, room.spawn, [], room.pickups, [], room.doors,
                     room.saves, [], landing_pad=room.ship or room.spawn,
                     decorations=room.decorations, rooms=rooms)
