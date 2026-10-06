"""Procedural art: ships."""

from __future__ import annotations

from ._base import *  # noqa: F401,F403


def _draw_hull(s, flame: bool = True) -> None:
    """Draw the side-view gunship on a 128x46 surface, nose to the right."""
    hull = (190, 196, 214)
    hull_dark = (96, 104, 130)
    hull_line = (132, 140, 166)
    accent = (90, 240, 255)

    # rear engine + flame (points -x, opposite travel)
    if flame:
        pygame.draw.polygon(s, (255, 150, 60), [(18, 23), (0, 15), (7, 23), (0, 31)])
        pygame.draw.polygon(s, (255, 228, 150), [(18, 23), (6, 19), (10, 23), (6, 27)])
    pygame.draw.rect(s, hull_dark, (15, 16, 13, 14), border_radius=3)
    pygame.draw.rect(s, (58, 64, 86) if flame else (40, 44, 60), (12, 19, 5, 8),
                     border_radius=2)

    # fins
    pygame.draw.polygon(s, hull_dark, [(52, 12), (60, 0), (74, 9)])
    pygame.draw.polygon(s, hull_dark, [(56, 31), (64, 44), (78, 31)])

    # main hull
    pygame.draw.polygon(s, hull_dark, [(20, 18), (44, 10), (98, 8), (120, 20),
                                       (114, 31), (48, 33), (24, 28)])
    pygame.draw.polygon(s, hull, [(26, 19), (46, 13), (96, 11), (114, 20),
                                  (108, 28), (50, 30), (28, 26)])
    pygame.draw.line(s, hull_line, (30, 25), (110, 20), 2)

    # cockpit canopy
    pygame.draw.polygon(s, accent, [(90, 12), (110, 18), (100, 25), (86, 20)])
    pygame.draw.polygon(s, (210, 250, 255), [(94, 15), (105, 18), (99, 23), (90, 20)])

    for x in range(38, 86, 12):
        pygame.draw.line(s, hull_line, (x, 15), (x, 28), 1)
    pygame.draw.circle(s, (255, 120, 120), (30, 22), 2)
    pygame.draw.circle(s, accent, (86, 18), 2)


def flying_gunship_surface() -> pygame.Surface:
    """Side view of the gunship in flight (rotated along its path)."""
    s = new_surface(128, 46)
    _draw_hull(s, flame=True)
    return s


def gunship_surface() -> pygame.Surface:
    """The same gunship, parked on the landing pad (engine off, gear down)."""
    w, h = 136, 64
    s = new_surface(w, h)
    hull = new_surface(128, 46)
    _draw_hull(hull, flame=False)
    s.blit(hull, (4, 4))

    hull_dark = (96, 104, 130)
    accent = (90, 240, 255)
    # landing struts
    for lx in (34, 96):
        pygame.draw.line(s, hull_dark, (lx, 40), (lx - 7, 58), 4)
        pygame.draw.line(s, hull_dark, (lx + 8, 40), (lx + 11, 58), 4)
        pygame.draw.rect(s, hull_dark, (lx - 10, 56, 25, 5), border_radius=2)
    # boarding ramp / under-bay light
    pygame.draw.ellipse(s, (80, 200, 255, 45), (42, 42, 52, 18))
    pygame.draw.line(s, accent, (50, 46), (86, 46), 2)
    return s
