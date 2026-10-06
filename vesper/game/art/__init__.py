"""Procedural, original pixel art.

Nothing here is traced, sampled or derived from any existing game.  Vesper's
heroine and every creature are generated from simple geometric primitives at
start-up, which keeps the project self-contained and free of third-party art
licences.  Split by concern under this package.
"""

from __future__ import annotations

from .black_hole import draw_black_hole
from .doors import door_frames
from .enemies import boss_art, crawler_art, flyer_art, jumper_art, turret_art
from .items import ITEM_COLORS, item_surface, missile_icon, projectile_surface
from .player import _hunter, morph_animations, player_animations
from .props import (SURFACE_DECOR, beacon_surface, crate_surface,
                    dead_tree_surface, gate_open_surface, gate_surface,
                    lamp_surface, mushroom_surface, puddle_surface,
                    ruin_pillar_surface, save_surface)
from .ships import flying_gunship_surface, gunship_surface
from .tiles import build_tile_surfaces

__all__ = [
    "player_animations",
    "morph_animations",
    "crawler_art",
    "flyer_art",
    "turret_art",
    "jumper_art",
    "boss_art",
    "ITEM_COLORS",
    "item_surface",
    "missile_icon",
    "projectile_surface",
    "build_tile_surfaces",
    "gate_surface",
    "gate_open_surface",
    "save_surface",
    "puddle_surface",
    "lamp_surface",
    "mushroom_surface",
    "dead_tree_surface",
    "ruin_pillar_surface",
    "crate_surface",
    "beacon_surface",
    "SURFACE_DECOR",
    "door_frames",
    "draw_black_hole",
    "gunship_surface",
    "flying_gunship_surface",
]
