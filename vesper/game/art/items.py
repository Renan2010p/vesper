"""Procedural art: items."""

from __future__ import annotations

from ._base import *  # noqa: F401,F403
from ._base import _rect


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


def missile_icon(size: int = 16) -> pygame.Surface:
    """A small missile/rocket glyph for the HUD counter."""
    s = new_surface(size, size)

    def px(v: float) -> int:
        return int(round(v * size / 16.0))

    body = (224, 228, 240)
    body_dark = (120, 128, 152)
    nose = (255, 138, 90)
    fin = (255, 176, 96)
    flame = (255, 214, 120)
    pygame.draw.polygon(s, nose, [(px(8), px(1)), (px(5), px(6)), (px(11), px(6))])
    pygame.draw.rect(s, body, (px(5), px(5), px(6), px(7)))
    pygame.draw.rect(s, body_dark, (px(5), px(9), px(6), px(1)))
    pygame.draw.circle(s, (90, 200, 255), (px(8), px(8)), max(1, px(1.6)))
    pygame.draw.polygon(s, fin, [(px(5), px(9)), (px(2), px(13)), (px(5), px(13))])
    pygame.draw.polygon(s, fin, [(px(11), px(9)), (px(14), px(13)), (px(11), px(13))])
    pygame.draw.polygon(s, flame, [(px(6), px(12)), (px(8), px(15)), (px(10), px(12))])
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
