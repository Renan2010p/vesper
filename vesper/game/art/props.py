"""Procedural art: props."""

from __future__ import annotations

from ._base import *  # noqa: F401,F403


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
