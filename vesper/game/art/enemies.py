"""Procedural art: enemies."""

from __future__ import annotations

from ._base import *  # noqa: F401,F403
from ._base import _rect


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


def zeres_art() -> Dict[str, Animation]:
    """Zeres — a winged raider that guards the station core (Ridley-like)."""
    def frame(flap: bool, glow: bool = True):
        w, h = 64, 44
        s = new_surface(w, h)
        wing = Bug
        wing_dark = BugDark
        wy = 3 if flap else 13
        pygame.draw.polygon(s, wing, [(30, 22), (10, wy), (2, wy + 8), (26, 31)])
        pygame.draw.polygon(s, wing_dark, [(30, 24), (13, wy + 5), (25, 31)])
        pygame.draw.polygon(s, wing, [(34, 22), (54, wy), (62, wy + 8), (38, 31)])
        pygame.draw.polygon(s, wing_dark, [(34, 24), (51, wy + 5), (39, 31)])
        # tail
        pygame.draw.polygon(s, MantaDark, [(44, 24), (64, 17), (64, 29), (46, 29)])
        # body
        pygame.draw.polygon(s, MantaDark, [(14, 20), (40, 13), (53, 24), (40, 35), (16, 31)])
        pygame.draw.polygon(s, Manta, [(18, 21), (40, 17), (49, 24), (40, 32), (20, 29)])
        # head + jaw
        pygame.draw.polygon(s, Manta, [(18, 20), (4, 22), (10, 31), (20, 31)])
        pygame.draw.polygon(s, MantaDark, [(4, 26), (18, 26), (16, 32), (4, 31)])
        pygame.draw.polygon(s, (240, 240, 245),
                            [(6, 26), (8, 30), (10, 26), (12, 30), (14, 26)])
        # eye
        pygame.draw.circle(s, (18, 10, 22), (16, 22), 4)
        pygame.draw.circle(s, BossEye if glow else (150, 90, 40), (15, 22), 2)
        # back spikes
        for i in range(5):
            x = 24 + i * 6
            pygame.draw.polygon(s, wing_dark, [(x, 15), (x + 2, 9), (x + 4, 15)])
        return s
    return {
        "idle": Animation([frame(False), frame(True)], fps=6.0),
        "angry": Animation([frame(False), frame(True)], fps=11.0),
    }


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
