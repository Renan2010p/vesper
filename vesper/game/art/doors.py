"""Procedural art: doors."""

from __future__ import annotations

from ._base import *  # noqa: F401,F403


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
