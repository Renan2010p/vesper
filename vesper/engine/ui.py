"""Small immediate-mode UI toolkit (text, bars, panels, menus)."""

from __future__ import annotations

from typing import Dict, Optional, Sequence, Tuple

import pygame

from .platform import Backend

Color = Tuple[int, int, int]


class Fonts:
    """Font cache backed by the active platform (no direct OS calls)."""

    def __init__(self, backend: Optional[Backend] = None) -> None:
        self.backend = backend
        self._cache: Dict[Tuple, object] = {}

    def get(self, size: int, bold: bool = False):
        key = (size, bold)
        font = self._cache.get(key)
        if font is None:
            font = self.backend.load_font(size, bold) if self.backend else None
            self._cache[key] = font
        return font

    def get_mono(self, size: int):
        key = ("mono", size)
        font = self._cache.get(key)
        if font is None:
            font = self.backend.load_mono_font(size) if self.backend else None
            self._cache[key] = font
        return font


def draw_text(surface, fonts: Fonts, text: str, pos, size=20, color=(235, 235, 245),
              center=False, bold=False, shadow=(0, 0, 0)) -> pygame.Rect:
    font = fonts.get(size, bold)
    if shadow is not None:
        shadow_surf = font.render(text, True, shadow)
        rect = shadow_surf.get_rect()
        if center:
            rect.center = pos
        else:
            rect.topleft = pos
        surface.blit(shadow_surf, (rect.x + 2, rect.y + 2))
    surf = font.render(text, True, color)
    rect = surf.get_rect()
    if center:
        rect.center = pos
    else:
        rect.topleft = pos
    surface.blit(surf, rect)
    return rect


def draw_bar(surface, x, y, w, h, ratio, fill: Color, back: Color = (30, 30, 45),
             border: Color = (12, 12, 20), segments: int = 0) -> None:
    ratio = max(0.0, min(1.0, ratio))
    pygame.draw.rect(surface, border, (x - 2, y - 2, w + 4, h + 4), border_radius=3)
    pygame.draw.rect(surface, back, (x, y, w, h), border_radius=2)
    fw = int(w * ratio)
    if fw > 0:
        pygame.draw.rect(surface, fill, (x, y, fw, h), border_radius=2)
    if segments > 1:
        for i in range(1, segments):
            gx = x + int(w * i / segments)
            pygame.draw.line(surface, border, (gx, y), (gx, y + h))


def draw_panel(surface, rect: pygame.Rect, fill=(16, 18, 30, 235), border=(90, 200, 220)) -> None:
    panel = pygame.Surface(rect.size, pygame.SRCALPHA)
    pygame.draw.rect(panel, fill, panel.get_rect(), border_radius=8)
    pygame.draw.rect(panel, border, panel.get_rect(), width=2, border_radius=8)
    surface.blit(panel, rect.topleft)


class Menu:
    def __init__(self, items: Sequence[str], index: int = 0, sound=None) -> None:
        self.items = list(items)
        self.index = index
        self.sound = sound

    def move(self, delta: int) -> None:
        if not self.items:
            return
        self.index = (self.index + delta) % len(self.items)
        if self.sound:
            self.sound("select")

    @property
    def selected(self) -> str:
        return self.items[self.index]

    def draw(self, surface, fonts: Fonts, center: Tuple[int, int], spacing: int = 34,
             size: int = 26) -> None:
        cx, cy = center
        start = cy - (len(self.items) - 1) * spacing // 2
        for i, label in enumerate(self.items):
            selected = i == self.index
            color = (255, 240, 170) if selected else (150, 160, 180)
            text = f"> {label} <" if selected else label
            draw_text(surface, fonts, text, (cx, start + i * spacing), size=size,
                      color=color, center=True, bold=selected)
