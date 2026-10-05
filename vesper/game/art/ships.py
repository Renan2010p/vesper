"""Procedural art: ships."""

from __future__ import annotations

from ._base import *  # noqa: F401,F403


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
