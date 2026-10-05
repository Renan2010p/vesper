"""Shared imports, palette and helpers for the art package."""

from __future__ import annotations

import math
import random
from typing import Dict, List, Tuple

import pygame

from vesper.engine.render import Animation
from vesper.engine.sprites import glow, new_surface, speckle

# -- palette ----------------------------------------------------------------
Suit = (196, 58, 92)
SuitDark = (126, 30, 62)
SuitLight = (240, 120, 148)
Armor = (226, 230, 244)
ArmorDark = (150, 158, 182)
Visor = (96, 240, 255)
VisorDim = (40, 150, 190)
Hair = (245, 196, 92)
Boot = (66, 68, 96)
Gun = (208, 214, 232)
Skin = (236, 190, 150)
Metal = (150, 156, 172)
MetalDark = (92, 98, 118)
Bug = (96, 168, 96)
BugDark = (52, 104, 66)
BugEye = (255, 90, 80)
Manta = (170, 96, 220)
MantaDark = (104, 56, 156)
MantaEye = (255, 240, 120)
JumperC = (224, 96, 72)
JumperDark = (150, 52, 40)
BossShell = (120, 128, 160)
BossCore = (255, 120, 90)
BossEye = (255, 230, 120)

_TS = 24


def _rect(surf, x, y, w, h, color):
    pygame.draw.rect(surf, color, (x, y, w, h))
