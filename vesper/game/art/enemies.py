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
