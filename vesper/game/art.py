"""Procedural, original pixel art.

Nothing here is traced, sampled or derived from any existing game.  Vesper's
heroine and every creature are generated from simple geometric primitives at
start-up, which keeps the project self-contained and free of third-party art
licences.
"""

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


# ---------------------------------------------------------------------------
# The heroine: "Vesper", bounty hunter
# ---------------------------------------------------------------------------

def _hunter(aim: str = "side", leg: int = 0, bob: int = 0, arm: int = 0,
            gun_len: int = 3, hurt: bool = False, blink: bool = False) -> pygame.Surface:
    """Build one 18x24 frame of the heroine, facing right."""
    s = new_surface(18, 24)
    bob = bob
    body = SuitLight if hurt else Suit
    dark = SuitDark
    visor = VisorDim if blink else Visor
    # legs ---------------------------------------------------------------
    ly = 17 + bob
    if leg == 0:      # standing
        _rect(s, 6, ly, 3, 6, dark)
        _rect(s, 10, ly, 3, 6, body)
    elif leg == 1:    # run A
        _rect(s, 4, ly, 3, 5, dark)
        _rect(s, 11, ly, 3, 6, body)
    elif leg == 2:    # run B
        _rect(s, 6, ly, 3, 6, dark)
        _rect(s, 10, ly, 3, 5, body)
    elif leg == 3:    # run C
        _rect(s, 8, ly, 3, 5, body)
        _rect(s, 4, ly + 1, 3, 5, dark)
    elif leg == 4:    # tucked / jump
        _rect(s, 6, ly - 1, 4, 4, dark)
        _rect(s, 10, ly - 1, 3, 4, body)
    elif leg == 5:    # dash (stretched)
        _rect(s, 3, ly + 1, 4, 3, dark)
        _rect(s, 11, ly, 4, 3, body)
    elif leg == 6:    # hanging / wall
        _rect(s, 6, ly, 3, 4, dark)
        _rect(s, 9, ly + 1, 3, 5, body)
    elif leg == 7:    # run D (left forward)
        _rect(s, 5, ly, 3, 5, dark)
        _rect(s, 12, ly + 1, 3, 5, body)
    elif leg == 8:    # run E (right forward)
        _rect(s, 8, ly, 3, 6, dark)
        _rect(s, 4, ly + 1, 3, 5, body)
    elif leg == 9:    # landing squash
        _rect(s, 4, ly + 2, 4, 4, dark)
        _rect(s, 10, ly + 2, 4, 4, body)
    _rect(s, 6, ly + 5, 3, 2, Boot)
    _rect(s, 10, ly + 5, 3, 2, Boot)

    # ponytail -----------------------------------------------------------
    if leg == 5:  # trailing behind while dashing
        _rect(s, 1, 6 + bob, 5, 3, Hair)
        _rect(s, 2, 9 + bob, 3, 3, Hair)
    else:
        _rect(s, 3, 5 + bob, 3, 3, Hair)
        _rect(s, 2, 7 + bob, 3, 6, Hair)

    # torso --------------------------------------------------------------
    _rect(s, 6, 9 + bob, 7, 8, body)
    _rect(s, 7, 10 + bob, 5, 4, ArmorDark)
    _rect(s, 6, 15 + bob, 7, 2, dark)
    # shoulder -----------------------------------------------------------
    _rect(s, 11, 9 + bob, 3, 3, Armor)

    # head ---------------------------------------------------------------
    _rect(s, 6, 3 + bob, 7, 6, Armor)
    _rect(s, 6, 3 + bob, 7, 2, dark)
    _rect(s, 7, 6 + bob, 5, 2, ArmorDark)

    # arm + gun by aim ---------------------------------------------------
    ay = 11 + bob + arm
    if aim == "side":
        _rect(s, 12, ay, 4, 3, dark)
        _rect(s, 14, ay, gun_len, 3, Gun)
        _rect(s, 9, 5 + bob, 4, 3, visor)
    elif aim == "up":
        _rect(s, 9, 7 + bob, 3, 5, dark)
        _rect(s, 8, 1 + bob, 3, 9, Gun)
        _rect(s, 8, 4 + bob, 5, 3, visor)
    elif aim == "down":
        _rect(s, 11, ay + 2, 4, 4, dark)
        _rect(s, 12, ay + 5, 3, 5, Gun)
        _rect(s, 9, 5 + bob, 4, 3, visor)
    elif aim == "updiag":
        _rect(s, 11, ay - 1, 4, 3, dark)
        _rect(s, 13, ay - 4, 3, 5, Gun)
        _rect(s, 9, 4 + bob, 4, 3, visor)
    elif aim == "downdiag":
        _rect(s, 11, ay + 1, 4, 3, dark)
        _rect(s, 13, ay + 3, 3, 5, Gun)
        _rect(s, 9, 5 + bob, 4, 3, visor)
    return s


def player_animations() -> Dict[str, Animation]:
    anims: Dict[str, Animation] = {}
    for aim in ("side", "up", "down"):
        # idle: gentle breathing with an occasional visor blink
        idle = [_hunter(aim, leg=0, bob=b) for b in (0, 0, 0, 1, 1, 0, 0, 0)]
        idle[4] = _hunter(aim, leg=0, bob=1, blink=True)
        anims[f"idle_{aim}"] = Animation(idle, fps=7.0)
        # run: six-frame leg cycle with arm swing
        run = [
            _hunter(aim, leg=1, bob=-1, arm=1),
            _hunter(aim, leg=0, bob=0, arm=0),
            _hunter(aim, leg=3, bob=1, arm=-1),
            _hunter(aim, leg=2, bob=0, arm=0),
            _hunter(aim, leg=8, bob=-1, arm=1),
            _hunter(aim, leg=7, bob=0, arm=0),
        ]
        anims[f"run_{aim}"] = Animation(run, fps=14.0)
        anims[f"jump_{aim}"] = Animation([_hunter(aim, leg=4, bob=0)], fps=1.0)
        anims[f"fall_{aim}"] = Animation([_hunter(aim, leg=6, bob=0)], fps=1.0)
    anims["dash"] = Animation([_hunter("side", leg=5, bob=0, gun_len=4)], fps=1.0)
    anims["hurt"] = Animation([_hunter("side", leg=6, bob=0, hurt=True)], fps=1.0)
    anims["land"] = Animation([_hunter("side", leg=9, bob=2),
                               _hunter("side", leg=0, bob=0)], fps=12.0, loop=False)
    anims["skid"] = Animation([_hunter("side", leg=3, bob=1, arm=-1)], fps=1.0)

    # spin jump: the heroine somersaults in mid-air
    ball = new_surface(18, 24)
    pygame.draw.circle(ball, SuitDark, (9, 12), 8)
    pygame.draw.circle(ball, Suit, (9, 12), 7)
    pygame.draw.circle(ball, ArmorDark, (9, 12), 4)
    pygame.draw.circle(ball, Visor, (9, 12), 2)
    pygame.draw.line(ball, Armor, (9, 4), (9, 8), 2)          # marker to read rotation
    pygame.draw.circle(ball, Boot, (5, 16), 2)
    pygame.draw.circle(ball, Boot, (13, 16), 2)
    spin = []
    for i in range(8):
        rotated = pygame.transform.rotate(ball, -45 * i)
        canvas = new_surface(18, 24)
        canvas.blit(rotated, rotated.get_rect(center=(9, 12)).topleft)
        spin.append(canvas)
    anims["spin"] = Animation(spin, fps=18.0)
    return anims


def morph_animations() -> Dict[str, Animation]:
    frames = []
    for i in range(4):
        s = new_surface(16, 16)
        r = 7 - i
        pygame.draw.circle(s, SuitDark, (8, 8), 7)
        pygame.draw.circle(s, Suit, (8, 8), 6)
        pygame.draw.circle(s, ArmorDark, (8, 8), 4)
        # rolling visor band
        ang = i * math.pi / 2
        vx = int(8 + math.cos(ang) * 4)
        vy = int(8 + math.sin(ang) * 4)
        pygame.draw.circle(s, Visor, (vx, vy), 2)
        frames.append(s)
    return {"morph": Animation(frames, fps=14.0)}


# ---------------------------------------------------------------------------
# Enemies
# ---------------------------------------------------------------------------

def crawler_art() -> Dict[str, Animation]:
    def frame(phase):
        s = new_surface(16, 14)
        _rect(s, 2, 5, 12, 6, Bug)
        _rect(s, 2, 5, 12, 2, BugDark)
        _rect(s, 3, 8, 10, 3, BugDark)
        _rect(s, 11, 6, 3, 3, BugEye)
        # legs
        for i in range(4):
            lx = 3 + i * 3
            off = 1 if (i + phase) % 2 == 0 else 0
            _rect(s, lx, 11 - off, 1, 3, BugDark)
        return s
    return {"idle": Animation([frame(0), frame(1)], fps=6.0)}


def flyer_art() -> Dict[str, Animation]:
    def frame(up):
        s = new_surface(20, 14)
        _rect(s, 7, 4, 6, 6, Manta)
        _rect(s, 7, 4, 6, 2, MantaDark)
        _rect(s, 10, 5, 3, 3, MantaEye)
        wy = 3 if up else 6
        pygame.draw.polygon(s, Manta, [(7, 6), (0, wy), (1, wy + 4), (7, 9)])
        pygame.draw.polygon(s, Manta, [(13, 6), (20, wy), (19, wy + 4), (13, 9)])
        pygame.draw.polygon(s, MantaDark, [(7, 7), (2, wy + 2), (7, 9)])
        pygame.draw.polygon(s, MantaDark, [(13, 7), (18, wy + 2), (13, 9)])
        return s
    return {"idle": Animation([frame(True), frame(False)], fps=8.0)}


def turret_art() -> Dict[str, Animation]:
    def frame(glow_on):
        s = new_surface(18, 18)
        _rect(s, 2, 12, 14, 5, MetalDark)
        _rect(s, 3, 12, 12, 3, Metal)
        _rect(s, 5, 5, 8, 8, Metal)
        _rect(s, 5, 5, 8, 2, MetalDark)
        _rect(s, 8, 1, 3, 6, MetalDark)
        _rect(s, 7, 6, 5, 5, (30, 30, 40))
        eye = (255, 90, 70) if glow_on else (150, 40, 40)
        _rect(s, 8, 7, 3, 3, eye)
        return s
    return {"idle": Animation([frame(True), frame(False)], fps=3.0)}


def jumper_art() -> Dict[str, Animation]:
    def frame(squash):
        w = 15 + (2 if squash else 0)
        h = 13 - (2 if squash else 0)
        s = new_surface(18, 16)
        x = (18 - w) // 2
        y = 16 - h
        pygame.draw.ellipse(s, JumperC, (x, y, w, h))
        pygame.draw.ellipse(s, JumperDark, (x + 2, y + h // 2, w - 4, h // 2))
        pygame.draw.circle(s, (255, 255, 255), (x + 4, y + 4), 2)
        pygame.draw.circle(s, (20, 20, 20), (x + 5, y + 4), 1)
        pygame.draw.circle(s, (255, 255, 255), (x + w - 5, y + 4), 2)
        pygame.draw.circle(s, (20, 20, 20), (x + w - 5, y + 4), 1)
        return s
    return {"idle": Animation([frame(False), frame(True)], fps=5.0)}


def boss_art() -> Dict[str, Animation]:
    def frame(t, eye=True):
        size = 56
        s = new_surface(size, size)
        c = size // 2
        pygame.draw.circle(s, MetalDark, (c, c), 25)
        pygame.draw.circle(s, BossShell, (c, c), 21)
        pygame.draw.circle(s, MetalDark, (c, c), 15)
        pygame.draw.circle(s, BossCore, (c, c), 11)
        pygame.draw.circle(s, (255, 190, 140), (c, c), 6)
        if eye:
            pygame.draw.circle(s, BossEye, (c, c), 3)
        # spikes
        for i in range(8):
            a = i * math.pi / 4 + t
            x1 = c + math.cos(a) * 21
            y1 = c + math.sin(a) * 21
            x2 = c + math.cos(a) * 28
            y2 = c + math.sin(a) * 28
            pygame.draw.line(s, BossShell, (x1, y1), (x2, y2), 4)
            pygame.draw.circle(s, BossEye, (int(x2), int(y2)), 2)
        return s
    return {
        "idle": Animation([frame(0.0), frame(0.4), frame(0.8)], fps=6.0),
        "angry": Animation([frame(0.0), frame(0.2), frame(0.4), frame(0.6)], fps=10.0),
    }


ENEMY_ART = {
    "crawler": crawler_art,
    "flyer": flyer_art,
    "turret": turret_art,
    "jumper": jumper_art,
    "warden": boss_art,
}


# ---------------------------------------------------------------------------
# Items / pickups
# ---------------------------------------------------------------------------

ITEM_COLORS = {
    "energy_tank": (120, 240, 150),
    "missile_tank": (255, 170, 90),
    "missile": (255, 170, 90),
    "charge": (255, 236, 130),
    "morph": (150, 220, 255),
    "grav_boots": (170, 150, 255),
    "dash": (255, 140, 200),
    "wall_grip": (150, 255, 220),
    "super_missile": (255, 210, 90),
    "core": (255, 120, 90),
    "map": (180, 220, 255),
}


def item_surface(item_id: str) -> pygame.Surface:
    color = ITEM_COLORS.get(item_id, (230, 230, 240))
    s = new_surface(20, 20)
    glow_s = glow(10, color, 150)
    s.blit(glow_s, (0, 0))
    if item_id in ("energy_tank", "missile_tank"):
        _rect(s, 6, 4, 8, 12, (40, 44, 60))
        _rect(s, 7, 5, 6, 10, color)
        _rect(s, 9, 3, 2, 2, (200, 200, 210))
        if item_id == "energy_tank":
            _rect(s, 9, 7, 2, 6, (255, 255, 255))
        else:
            _rect(s, 8, 9, 4, 2, (255, 255, 255))
    elif item_id == "core":
        pygame.draw.polygon(s, color, [(10, 2), (17, 10), (10, 18), (3, 10)])
        pygame.draw.polygon(s, (255, 220, 180), [(10, 6), (14, 10), (10, 14), (6, 10)])
    elif item_id in ("charge", "dash", "morph", "grav_boots", "wall_grip",
                     "super_missile", "missile"):
        pygame.draw.circle(s, (30, 34, 48), (10, 10), 8)
        pygame.draw.circle(s, color, (10, 10), 6)
        pygame.draw.circle(s, (255, 255, 255), (10, 10), 3)
        # small glyph per ability
        if item_id == "missile":
            _rect(s, 8, 6, 4, 8, (60, 40, 20))
            _rect(s, 9, 4, 2, 3, (255, 240, 200))
        elif item_id == "dash":
            _rect(s, 6, 9, 8, 2, (255, 255, 255))
            _rect(s, 8, 6, 4, 2, (255, 255, 255))
        elif item_id == "grav_boots":
            _rect(s, 6, 11, 3, 4, (255, 255, 255))
            _rect(s, 11, 11, 3, 4, (255, 255, 255))
        elif item_id == "wall_grip":
            _rect(s, 7, 6, 2, 8, (255, 255, 255))
            _rect(s, 11, 6, 2, 8, (255, 255, 255))
        elif item_id == "morph":
            pygame.draw.circle(s, (255, 255, 255), (10, 10), 4)
        elif item_id == "charge":
            _rect(s, 9, 5, 2, 10, (255, 255, 255))
            _rect(s, 6, 9, 8, 2, (255, 255, 255))
    elif item_id == "map":
        _rect(s, 4, 5, 12, 10, (250, 250, 250))
        _rect(s, 4, 5, 12, 2, (200, 200, 210))
    return s


def projectile_surface(kind: str) -> pygame.Surface:
    if kind == "beam":
        s = new_surface(10, 6)
        _rect(s, 0, 2, 10, 2, (180, 250, 255))
        _rect(s, 2, 1, 6, 4, (120, 230, 255))
        return s
    if kind == "charged":
        s = new_surface(18, 12)
        _rect(s, 0, 4, 18, 4, (120, 230, 255))
        _rect(s, 2, 2, 14, 8, (200, 250, 255))
        _rect(s, 6, 4, 6, 4, (255, 255, 255))
        return s
    if kind == "missile":
        s = new_surface(14, 8)
        _rect(s, 2, 2, 9, 4, (220, 220, 230))
        pygame.draw.polygon(s, (255, 120, 80), [(11, 2), (14, 4), (11, 6)])
        pygame.draw.polygon(s, (255, 220, 120), [(2, 2), (0, 4), (2, 6)])
        return s
    if kind == "enemy":
        s = new_surface(10, 10)
        pygame.draw.circle(s, (255, 110, 90), (5, 5), 4)
        pygame.draw.circle(s, (255, 230, 150), (5, 5), 2)
        return s
    if kind == "boss_orb":
        s = new_surface(16, 16)
        pygame.draw.circle(s, (255, 90, 130), (8, 8), 7)
        pygame.draw.circle(s, (255, 200, 120), (8, 8), 4)
        return s
    return new_surface(8, 8, (255, 255, 255))


# ---------------------------------------------------------------------------
# Tiles
# ---------------------------------------------------------------------------

def build_tile_surfaces(tileset, tile: int = _TS) -> Dict[int, pygame.Surface]:
    surfaces: Dict[int, pygame.Surface] = {}
    rng = random.Random(1337)
    for tile_id, definition in tileset.defs().items():
        if tile_id == 0:
            continue
        if definition.name == "surface_top":
            st = new_surface(tile, tile)
            st.fill(definition.color)
            speckle(st, definition.color2, count=9, rng=rng, size=2)
            # mossy / grassy top edge
            pygame.draw.rect(st, (52, 104, 74), (0, 0, tile, 3))
            pygame.draw.line(st, (86, 168, 116), (0, 0), (tile - 1, 0))
            for gx in range(1, tile, 4):
                pygame.draw.line(st, (74, 150, 104), (gx, 0), (gx, 4 + (gx % 3)))
            # a couple of pebbles
            pygame.draw.circle(st, definition.color2, (6, 12), 2)
            pygame.draw.circle(st, definition.color2, (17, 16), 1)
            surfaces[tile_id] = st
            continue
        s = new_surface(tile, tile)
        color = definition.color
        color2 = definition.color2
        s.fill(color)
        speckle(s, color2, count=10, rng=rng, size=2)
        # top highlight / bottom shade for solid blocks
        if definition.solid:
            pygame.draw.line(s, tuple(min(255, c + 26) for c in color), (0, 0), (tile - 1, 0))
            pygame.draw.line(s, tuple(max(0, c - 30) for c in color), (0, tile - 1), (tile - 1, tile - 1))
            pygame.draw.line(s, color2, (0, 2), (tile - 1, 2))
        if definition.oneway:
            s = new_surface(tile, 8)
            s.fill(color2)
            pygame.draw.line(s, color, (0, 0), (tile - 1, 0))
            pygame.draw.line(s, color, (0, 1), (tile - 1, 1))
        elif definition.hazard:
            s = new_surface(tile, tile)
            if definition.name in ("spike",):
                for i in range(3):
                    x = i * 8
                    pygame.draw.polygon(s, color, [(x, tile), (x + 4, 4), (x + 8, tile)])
                    pygame.draw.polygon(s, color2, [(x + 2, tile), (x + 4, 8), (x + 6, tile)])
            else:  # lava
                s.fill(color)
                for i in range(4):
                    yy = 4 + i * 5
                    pygame.draw.line(s, color2, (0, yy), (tile, yy), 1)
                speckle(s, (255, 240, 180), 6, rng)
        surfaces[tile_id] = s
    return surfaces


# ---------------------------------------------------------------------------
# Props
# ---------------------------------------------------------------------------

def gate_surface(w: int, h: int, color=(150, 240, 255)) -> pygame.Surface:
    s = new_surface(w, h)
    pygame.draw.rect(s, (40, 46, 66), (0, 0, w, h), border_radius=4)
    pygame.draw.rect(s, (24, 28, 44), (2, 2, w - 4, h - 4), border_radius=3)
    for y in range(3, h - 3, 6):
        pygame.draw.line(s, (60, 66, 92), (3, y), (w - 4, y))
    pygame.draw.rect(s, color, (0, 0, w, h), width=2, border_radius=4)
    # energy seams
    pygame.draw.line(s, color, (w // 2, 2), (w // 2, h - 2))
    return s


def gate_open_surface(w: int, h: int, color=(150, 240, 255)) -> pygame.Surface:
    s = new_surface(w, h)
    pygame.draw.rect(s, (*color, 60), (0, 0, w, h), border_radius=4)
    pygame.draw.rect(s, color, (0, 0, w, h), width=1, border_radius=4)
    return s


def save_surface() -> pygame.Surface:
    s = new_surface(20, 26)
    pygame.draw.rect(s, (60, 70, 100), (1, 1, 18, 24), border_radius=3)
    pygame.draw.rect(s, (110, 220, 180), (3, 3, 14, 20), border_radius=2)
    pygame.draw.rect(s, (24, 34, 40), (5, 6, 10, 8))
    pygame.draw.circle(s, (240, 255, 240), (10, 10), 3)
    pygame.draw.rect(s, (24, 34, 40), (6, 17, 8, 4))
    return s


def spawn_pad_surface() -> pygame.Surface:
    s = new_surface(26, 14)
    pygame.draw.ellipse(s, (30, 36, 54), (0, 2, 26, 12))
    pygame.draw.ellipse(s, (90, 240, 255), (2, 4, 22, 8), width=1)
    pygame.draw.circle(s, (90, 240, 255), (13, 8), 2)
    return s


def breaker_surface() -> pygame.Surface:
    s = new_surface(20, 20)
    pygame.draw.polygon(s, (255, 190, 120), [(10, 2), (17, 10), (10, 18), (3, 10)])
    pygame.draw.polygon(s, (120, 70, 30), [(10, 6), (14, 10), (10, 14), (6, 10)])
    return s


def puddle_surface(w: int = 44) -> pygame.Surface:
    s = new_surface(w, 10)
    pygame.draw.ellipse(s, (26, 40, 58), (0, 0, w, 10))
    pygame.draw.ellipse(s, (70, 118, 158), (0, 1, w, 6), 1)
    pygame.draw.line(s, (150, 200, 230), (4, 3), (w // 2, 3))
    pygame.draw.line(s, (110, 160, 200), (w // 2 + 4, 6), (w - 6, 6))
    return s


def lamp_surface() -> pygame.Surface:
    s = new_surface(14, 30)
    pygame.draw.rect(s, (36, 42, 58), (5, 9, 4, 21))
    pygame.draw.rect(s, (58, 66, 88), (4, 27, 6, 3))
    pygame.draw.circle(s, (70, 200, 230), (7, 8), 6)
    pygame.draw.circle(s, (150, 245, 255), (7, 8), 4)
    pygame.draw.circle(s, (240, 255, 255), (7, 8), 2)
    return s


def mushroom_surface() -> pygame.Surface:
    s = new_surface(16, 16)
    pygame.draw.rect(s, (176, 158, 122), (7, 8, 3, 7))
    pygame.draw.ellipse(s, (96, 176, 236), (1, 2, 14, 9))
    pygame.draw.ellipse(s, (176, 226, 255), (3, 4, 7, 4))
    pygame.draw.circle(s, (220, 250, 255), (11, 6), 1)
    return s


def dead_tree_surface() -> pygame.Surface:
    s = new_surface(30, 52)
    trunk = (70, 58, 48)
    dark = (50, 42, 36)
    pygame.draw.polygon(s, trunk, [(12, 52), (14, 12), (17, 52)])
    pygame.draw.line(s, dark, (14, 46), (14, 16), 1)
    pygame.draw.line(s, trunk, (14, 24), (3, 8), 3)
    pygame.draw.line(s, trunk, (14, 30), (25, 14), 3)
    pygame.draw.line(s, trunk, (14, 16), (9, 2), 2)
    pygame.draw.line(s, dark, (3, 8), (1, 3), 2)
    return s


def ruin_pillar_surface(h: int = 44) -> pygame.Surface:
    s = new_surface(20, h)
    stone = (150, 146, 138)
    stone2 = (104, 100, 94)
    pygame.draw.rect(s, stone, (2, 0, 16, h))
    pygame.draw.rect(s, stone2, (2, 0, 16, h), 2)
    for y in range(5, h, 9):
        pygame.draw.line(s, stone2, (4, y), (16, y), 1)
    # broken top
    pygame.draw.polygon(s, (0, 0, 0, 0), [(2, 0), (10, 0), (6, 6)])
    pygame.draw.circle(s, stone2, (8, 12), 2)
    return s


def crate_surface() -> pygame.Surface:
    s = new_surface(22, 20)
    metal = (96, 104, 128)
    metal2 = (62, 68, 90)
    pygame.draw.rect(s, metal, (0, 0, 22, 20))
    pygame.draw.rect(s, metal2, (0, 0, 22, 20), 2)
    pygame.draw.line(s, metal2, (0, 0), (22, 20), 2)
    pygame.draw.line(s, metal2, (22, 0), (0, 20), 2)
    pygame.draw.circle(s, (90, 240, 255), (11, 10), 2)
    return s


def beacon_surface() -> pygame.Surface:
    s = new_surface(18, 34)
    pygame.draw.rect(s, (60, 66, 88), (7, 12, 4, 22))
    pygame.draw.circle(s, (150, 60, 50), (9, 9), 7)
    pygame.draw.circle(s, (255, 120, 90), (9, 9), 5)
    pygame.draw.circle(s, (255, 230, 190), (9, 9), 2)
    return s


SURFACE_DECOR = {
    "puddle": puddle_surface,
    "lamp": lamp_surface,
    "mushroom": mushroom_surface,
    "tree": dead_tree_surface,
    "pillar": ruin_pillar_surface,
    "crate": crate_surface,
    "beacon": beacon_surface,
}


def _door_panel(s, x, y, w, h, slab, slab2) -> None:
    x, y, w, h = int(x), int(y), int(w), int(h)
    if w <= 0 or h <= 0:
        return
    pygame.draw.rect(s, slab, (x, y, w, h))
    if h >= w:
        for yy in range(y + 4, y + h - 2, 7):
            pygame.draw.line(s, slab2, (x + 1, yy), (x + w - 2, yy))
    else:
        for xx in range(x + 4, x + w - 2, 7):
            pygame.draw.line(s, slab2, (xx, y + 1), (xx, y + h - 2))
    pygame.draw.rect(s, slab2, (x, y, w, h), 1)


def _door_frame(w: int, h: int, color, t: float) -> pygame.Surface:
    """One animation frame.  ``t`` runs 0 (shut) .. 1 (fully open)."""
    s = new_surface(w, h)
    frame = (78, 84, 108)
    frame2 = (52, 58, 80)
    slab = (108, 116, 142)
    slab2 = (80, 86, 112)
    dark = (22, 26, 40)
    vertical = h >= w

    pygame.draw.rect(s, dark, (0, 0, w, h), border_radius=4)
    pygame.draw.rect(s, frame, (0, 0, w, h), width=4, border_radius=4)
    for bx, by in ((6, 6), (w - 7, 6), (6, h - 7), (w - 7, h - 7)):
        pygame.draw.circle(s, frame2, (bx, by), 2)

    if vertical:
        gap = max(0, h - 18) * t
        top_end = h / 2 - gap / 2
        bot_start = h / 2 + gap / 2
        _door_panel(s, 5, 5, w - 10, top_end - 5, slab, slab2)
        _door_panel(s, 5, bot_start, w - 10, (h - 5) - bot_start, slab, slab2)
        pygame.draw.line(s, frame2, (5, int(top_end)), (w - 6, int(top_end)), 2)
        pygame.draw.line(s, frame2, (5, int(bot_start)), (w - 6, int(bot_start)), 2)
        if gap > 1:
            pygame.draw.line(s, color, (5, int(top_end)), (w - 6, int(top_end)), 3)
            pygame.draw.line(s, color, (5, int(bot_start)), (w - 6, int(bot_start)), 3)
    else:
        gap = max(0, w - 18) * t
        left_end = w / 2 - gap / 2
        right_start = w / 2 + gap / 2
        _door_panel(s, 5, 5, left_end - 5, h - 10, slab, slab2)
        _door_panel(s, right_start, 5, (w - 5) - right_start, h - 10, slab, slab2)
        pygame.draw.line(s, frame2, (int(left_end), 5), (int(left_end), h - 6), 2)
        pygame.draw.line(s, frame2, (int(right_start), 5), (int(right_start), h - 6), 2)
        if gap > 1:
            pygame.draw.line(s, color, (int(left_end), 5), (int(left_end), h - 6), 3)
            pygame.draw.line(s, color, (int(right_start), 5), (int(right_start), h - 6), 3)

    # central coloured "eye" — the classic Super Metroid door light
    if t < 0.7:
        radius = max(6, int((min(w, h) // 2 - 3) * (1 - 0.5 * t)))
        cx, cy = w // 2, h // 2
        pygame.draw.circle(s, dark, (cx, cy), radius + 4)
        pygame.draw.circle(s, frame, (cx, cy), radius + 3)
        pygame.draw.circle(s, frame2, (cx, cy), radius + 1, 2)
        pygame.draw.circle(s, color, (cx, cy), radius)
        pygame.draw.circle(s, (245, 255, 255), (cx, cy), max(2, radius // 3))
    return s


def door_frames(w: int, h: int, color, steps: int = 7) -> list:
    """Closed..open animation frames for a hatch."""
    return [_door_frame(w, h, color, i / (steps - 1)) for i in range(steps)]


_BH_CACHE: dict = {}
_BH_OVERLAY: dict = {}


def _black_hole_base(r: int) -> pygame.Surface:
    """Static parts (glow, disk, lensing) cached per radius."""
    cached = _BH_CACHE.get(r)
    if cached is not None:
        return cached
    size = int(r * 16)
    layer = pygame.Surface((size, size), pygame.SRCALPHA)
    c = size // 2

    # soft radial glow that fades fully to transparent (no square edge)
    steps = 70
    for k in range(steps, 0, -1):
        f = k / steps
        rr = r * (1.0 + f * 6.0)
        a = int(72 * (1 - f) ** 2.3)
        if a <= 0:
            continue
        pygame.draw.circle(layer, (255, 150, 85, a), (c, c), int(rr))

    # accretion disk: hot blue-white inner -> orange outer
    for k in range(40):
        f = k / 39
        rr = r * (1.12 + f * 2.3)
        a = int(175 * (1 - f) ** 0.85)
        col = (255, int(238 - 120 * f), int(228 - 170 * f))
        rect = (c - rr, c - rr * 0.26, rr * 2, rr * 0.52)
        pygame.draw.ellipse(layer, (*col, a), rect, 2)

    # Doppler beaming: the approaching side (right) is brighter
    for k in range(16):
        f = k / 15
        rr = r * (1.15 + f * 2.0)
        a = int(130 * (1 - f))
        rect = (c - rr, c - rr * 0.26, rr * 2, rr * 0.52)
        pygame.draw.arc(layer, (255, 250, 235, a), rect, -0.9, 0.9, 3)

    # gravitational lensing: the far side of the disk arcs over the top
    pygame.draw.arc(layer, (255, 226, 188, 180),
                    (c - r * 1.18, c - r * 1.22, r * 2.36, r * 1.3), 0.5, 2.64, 3)
    pygame.draw.arc(layer, (255, 210, 170, 130),
                    (c - r * 1.32, c - r * 1.46, r * 2.64, r * 1.6), 0.72, 2.42, 2)

    _BH_CACHE[r] = layer
    return layer


def draw_black_hole(surface, cx: int, cy: int, r: int, t: float) -> None:
    """Animated black hole: accretion disk, lensing and orbiting particles.

    Far-side particles are occluded by the event horizon; near-side ones pass in
    front of it.
    """
    base = _black_hole_base(r)
    c = base.get_width() // 2
    surface.blit(base, (cx - c, cy - c))

    size = int(r * 4)
    overlay = _BH_OVERLAY.get(r)
    if overlay is None:
        overlay = pygame.Surface((size, size), pygame.SRCALPHA)
        _BH_OVERLAY[r] = overlay
    overlay.fill((0, 0, 0, 0))
    cc = size // 2

    sparks = []
    for i in range(38):
        speed = 0.9 + (i % 4) * 0.3
        ang = t * speed + i * 0.19
        rr = r * (1.35 + (i % 6) * 0.26)
        trail = []
        for j in range(5):
            aa = ang - j * 0.05
            trail.append((cc + math.cos(aa) * rr, cc + math.sin(aa) * rr * 0.32))
        sparks.append((trail, math.sin(ang)))

    def draw_spark(trail):
        for j, (x, y) in enumerate(trail):
            a = int(235 * (1 - j / 5))
            col = (255, 240, 205, a) if j == 0 else (255, 180, 120, a)
            pygame.draw.circle(overlay, col, (int(x), int(y)), max(1, 3 - j))

    for trail, depth in sparks:
        if depth < 0:
            draw_spark(trail)

    # event horizon + photon ring
    pygame.draw.circle(overlay, (0, 0, 0, 255), (cc, cc), int(r))
    pygame.draw.circle(overlay, (215, 200, 255, 215), (cc, cc), int(r) + 1, 2)

    for trail, depth in sparks:
        if depth >= 0:
            draw_spark(trail)

    surface.blit(overlay, (cx - cc, cy - cc))


def gunship_surface() -> pygame.Surface:
    """Vesper's gunship, hovering above the ground with a lit under-bay.

    Original design -- a heavy lander that floats on thrusters, leaving room to
    stand beneath it.
    """
    w, h = 184, 94
    s = new_surface(w, h)
    hull = (150, 158, 182)
    hull_dark = (88, 96, 122)
    hull_line = (112, 120, 148)
    accent = (90, 240, 255)
    bay = (16, 20, 32)

    # downward thruster glow (why it hovers)
    for i, alpha in ((0, 60), (1, 90), (2, 120)):
        rect = (w // 2 - 54 + i * 8, 74 + i * 3, 108 - i * 16, 14 - i * 3)
        pygame.draw.ellipse(s, (90, 200, 255, alpha), rect)

    # short landing struts (do not touch the ground)
    pygame.draw.line(s, hull_dark, (44, 50), (36, 70), 4)
    pygame.draw.line(s, hull_dark, (140, 50), (148, 70), 4)
    pygame.draw.rect(s, hull_dark, (30, 68, 16, 5), border_radius=2)
    pygame.draw.rect(s, hull_dark, (138, 68, 16, 5), border_radius=2)

    # main hull
    pygame.draw.polygon(s, hull_dark,
                        [(8, 30), (30, 10), (122, 6), (164, 20), (172, 36),
                         (152, 48), (34, 50), (10, 42)])
    pygame.draw.polygon(s, hull,
                        [(16, 30), (36, 14), (118, 10), (158, 22), (162, 34),
                         (146, 42), (38, 44), (18, 38)])
    pygame.draw.line(s, hull_line, (20, 36), (152, 30), 2)

    # under-bay opening where the heroine boards
    pygame.draw.polygon(s, bay, [(62, 44), (118, 44), (112, 66), (68, 66)])
    pygame.draw.line(s, accent, (66, 66), (114, 66), 2)
    pygame.draw.line(s, hull_line, (64, 46), (116, 46), 2)

    # cockpit canopy + engines
    pygame.draw.polygon(s, accent, [(120, 16), (148, 20), (152, 30), (118, 28)])
    pygame.draw.polygon(s, (200, 250, 255), [(126, 18), (140, 21), (142, 27), (124, 26)])
    pygame.draw.rect(s, hull_dark, (6, 22, 14, 16), border_radius=3)
    pygame.draw.polygon(s, (255, 150, 70), [(4, 24), (0, 30), (4, 36)])
    pygame.draw.polygon(s, (255, 220, 150), [(2, 27), (0, 30), (2, 33)])
    pygame.draw.polygon(s, hull_dark, [(72, 6), (88, -2), (98, 6)])

    for x in range(42, 120, 16):
        pygame.draw.line(s, hull_line, (x, 16), (x, 42), 1)
    pygame.draw.circle(s, accent, (162, 30), 2)
    pygame.draw.circle(s, (255, 120, 120), (12, 26), 2)
    return s


def ship_surface() -> pygame.Surface:
    """Small scout craft (legacy)."""
    return gunship_surface()
