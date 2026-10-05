"""Surface helpers used to build procedural, original artwork at runtime."""

from __future__ import annotations

import random
from typing import Tuple

import pygame

Color = Tuple[int, int, int]


def new_surface(w: int, h: int, color: Color | None = None, alpha: int = 255) -> pygame.Surface:
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    if color is not None:
        surf.fill((*color, alpha))
    return surf


def tint(surface: pygame.Surface, color: Color, amount: float = 0.5) -> pygame.Surface:
    out = surface.copy()
    layer = pygame.Surface(out.get_size(), pygame.SRCALPHA)
    layer.fill((*color, int(255 * amount)))
    out.blit(layer, (0, 0))
    return out


def outline(surface: pygame.Surface, color: Color = (10, 10, 18)) -> pygame.Surface:
    mask = pygame.mask.from_surface(surface)
    sil = mask.to_surface(setcolor=(*color, 255), unsetcolor=(0, 0, 0, 0))
    out = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
    for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        out.blit(sil, (dx, dy))
    out.blit(surface, (0, 0))
    return out


def horizontal_gradient(w: int, h: int, left: Color, right: Color) -> pygame.Surface:
    surf = pygame.Surface((w, h))
    for x in range(w):
        t = x / max(1, w - 1)
        color = (int(left[0] + (right[0] - left[0]) * t),
                 int(left[1] + (right[1] - left[1]) * t),
                 int(left[2] + (right[2] - left[2]) * t))
        pygame.draw.line(surf, color, (x, 0), (x, h))
    return surf


def vertical_gradient(w: int, h: int, top: Color, bottom: Color) -> pygame.Surface:
    surf = pygame.Surface((w, h))
    for y in range(h):
        t = y / max(1, h - 1)
        color = (int(top[0] + (bottom[0] - top[0]) * t),
                 int(top[1] + (bottom[1] - top[1]) * t),
                 int(top[2] + (bottom[2] - top[2]) * t))
        pygame.draw.line(surf, color, (0, y), (w, y))
    return surf


def speckle(surface: pygame.Surface, color: Color, count: int = 40, rng=None,
            size: int = 1) -> None:
    rng = rng or random
    for _ in range(count):
        x = rng.randrange(surface.get_width())
        y = rng.randrange(surface.get_height())
        pygame.draw.rect(surface, color, (x, y, size, size))


def glow(radius: int, color: Color, alpha: int = 180) -> pygame.Surface:
    size = radius * 2
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    for r in range(radius, 0, -1):
        a = int(alpha * (1 - r / radius) ** 1.6)
        pygame.draw.circle(surf, (*color, a), (radius, radius), r)
    return surf


def render_outline_text(font: pygame.font.Font, text: str, color: Color,
                        outline_color: Color) -> pygame.Surface:
    base = font.render(text, True, color)
    out = pygame.Surface((base.get_width() + 2, base.get_height() + 2), pygame.SRCALPHA)
    shadow = font.render(text, True, outline_color)
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            out.blit(shadow, (dx + 1, dy + 1))
    out.blit(base, (1, 1))
    return out
