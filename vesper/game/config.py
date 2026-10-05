"""Tunable constants and palette for Vesper."""

from __future__ import annotations

from typing import Dict, Tuple

TITLE = "VESPER — Depths of Nara  ·  RL PROJECTS"

# -- rendering --------------------------------------------------------------
LOGICAL_W = 512
LOGICAL_H = 288
TILE = 24
FPS = 60

# -- tile ids ---------------------------------------------------------------
T_EMPTY = 0
T_ROCK = 1
T_ROCK_DARK = 2
T_METAL = 3
T_ICE = 4
T_SPIKE = 5
T_LAVA = 6
T_CRYSTAL = 7         # breakable by missiles
T_ROCK_FG = 8         # foreground silhouette
T_ONEWAY = 9          # one-way platform
T_VINE = 10           # decorative background
T_GRATE = 11          # background grate (walk-through)
T_BOSS_ARMOR = 13     # unbreakable boss arena plating
T_SURFACE = 14        # brown surface rock
T_RUIN = 15           # pale alien ruin stone
T_MOSS = 16           # decorative moss (background)
T_SURFACE_TOP = 17    # surface rock with a mossy top edge

ZONE_COLORS: Dict[str, Tuple[Tuple[int, int, int], Tuple[int, int, int]]] = {
    "surface": ((8, 10, 24), (36, 30, 48)),
    "cave": ((8, 8, 14), (26, 22, 32)),
    "landing": ((14, 18, 32), (28, 24, 30)),
    "verdant": ((10, 26, 22), (16, 44, 34)),
    "hive": ((30, 14, 14), (52, 20, 18)),
    "shaft": ((16, 14, 30), (30, 24, 48)),
    "vault": ((12, 24, 40), (28, 52, 74)),
    "furnace": ((34, 12, 10), (70, 26, 12)),
    "aegis": ((18, 12, 34), (44, 20, 60)),
    "unknown": ((10, 12, 22), (22, 16, 30)),
}

#: hatch (door) light colours by required weapon tier
DOOR_COLORS: Dict[str, Tuple[int, int, int]] = {
    "any": (96, 190, 255),
    "missile": (255, 104, 96),
    "super": (255, 214, 110),
}

#: weapon tier ranking used by hatches (higher opens lower-tier doors)
WEAPON_TIER: Dict[str, int] = {
    "beam": 0,
    "charged": 0,
    "missile": 1,
    "super_missile": 2,
}
TIER_NAME = ["any", "missile", "super"]

# -- physics tuning ---------------------------------------------------------
GRAVITY = 2200.0
RUN_SPEED = 190.0
AIR_ACCEL = 900.0
GROUND_ACCEL = 1600.0
GROUND_FRICTION = 2000.0
JUMP_SPEED = 700.0
JUMP_CUT = 0.45          # multiply upward velocity on early release
DASH_SPEED = 620.0
DASH_TIME = 0.22
DASH_COOLDOWN = 0.55
MAX_FALL = 900.0
COYOTE_TIME = 0.10
JUMP_BUFFER = 0.12
WALL_SLIDE_SPEED = 120.0
WALL_JUMP_X = 260.0
WALL_JUMP_Y = 620.0
CHARGE_TIME = 0.75
MORPH_SPEED = 150.0

PLAYER_W = 14
PLAYER_H = 22

# -- combat -----------------------------------------------------------------
BASE_HEALTH = 99
ENERGY_PER_TANK = 100
BASE_MISSILES = 0
MISSILES_PER_TANK = 5
DAMAGE_INVULN = 0.85
MISSILE_DAMAGE = 20
CHARGE_DAMAGE = 30
BEAM_DAMAGE = 5

CORE_GOAL = 2   # cores needed to open the final gate

#: When True the world contains only the Nara Surface (no underground yet).
#: Flip to False to re-enable the caverns, boss and full progression.
SURFACE_ONLY = True
