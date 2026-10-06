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


def flying_gunship_surface() -> pygame.Surface:
    """Side view of the gunship in flight, nose to the right and a lit engine.

    Used by the intro fly-by: it is drawn facing +x so it can be rotated along
    its flight path, like Samus's gunship descending toward the planet.
    """
    w, h = 128, 46
    s = new_surface(w, h)
    hull = (190, 196, 214)
    hull_dark = (96, 104, 130)
    hull_line = (132, 140, 166)
    accent = (90, 240, 255)

    # rear engine flame (points -x, opposite travel)
    pygame.draw.polygon(s, (255, 150, 60), [(18, 23), (0, 15), (7, 23), (0, 31)])
    pygame.draw.polygon(s, (255, 228, 150), [(18, 23), (6, 19), (10, 23), (6, 27)])

    # engine block
    pygame.draw.rect(s, hull_dark, (15, 16, 13, 14), border_radius=3)
    pygame.draw.rect(s, (58, 64, 86), (12, 19, 5, 8), border_radius=2)

    # fins (top and bottom, near the tail)
    pygame.draw.polygon(s, hull_dark, [(52, 12), (60, 0), (74, 9)])
    pygame.draw.polygon(s, hull_dark, [(56, 31), (64, 44), (78, 31)])

    # main hull
    pygame.draw.polygon(s, hull_dark, [(20, 18), (44, 10), (98, 8), (120, 20),
                                       (114, 31), (48, 33), (24, 28)])
    pygame.draw.polygon(s, hull, [(26, 19), (46, 13), (96, 11), (114, 20),
                                  (108, 28), (50, 30), (28, 26)])
    pygame.draw.line(s, hull_line, (30, 25), (110, 20), 2)

    # cockpit canopy near the nose
    pygame.draw.polygon(s, accent, [(90, 12), (110, 18), (100, 25), (86, 20)])
    pygame.draw.polygon(s, (210, 250, 255), [(94, 15), (105, 18), (99, 23), (90, 20)])

    # panel lines and running lights
    for x in range(38, 86, 12):
        pygame.draw.line(s, hull_line, (x, 15), (x, 28), 1)
    pygame.draw.circle(s, (255, 120, 120), (30, 22), 2)
    pygame.draw.circle(s, accent, (86, 18), 2)
    return s
