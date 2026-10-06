"""Scripted cutscenes: the distress story, the flight to Zeres Station and
the escape as the station blows up.

A cutscene is just a scene that shows pages of text over a small procedural
animation, then hands off to the next scene.  Anything can call one with
``switch_scene("<name>", slot=...)``.
"""

from __future__ import annotations

import math
import random

import pygame

from vesper.engine.platform import EventType
from vesper.engine.scene import Scene
from vesper.engine.sprites import vertical_gradient
from vesper.engine.ui import draw_panel, draw_text

from .. import art, i18n

PAGE_TIME = 4.6


def _draw_station(surface, cx, cy, r, t, damaged=False) -> None:
    if r < 4:
        return
    ring = (120, 92, 92) if damaged else (150, 162, 188)
    pygame.draw.circle(surface, ring, (cx, cy), r, max(2, r // 10))
    pygame.draw.circle(surface, (58, 68, 98), (cx, cy), r, max(1, r // 22))
    pygame.draw.circle(surface, (110, 124, 156), (cx, cy), max(2, r // 4))
    pygame.draw.circle(surface, (90, 240, 255), (cx, cy), max(1, r // 8))
    for i in range(4):
        a = t * 0.5 + i * math.pi / 2
        pygame.draw.line(surface, ring, (cx, cy),
                         (cx + math.cos(a) * r, cy + math.sin(a) * r), max(1, r // 12))
    for i in range(10):
        a = t * 0.8 + i * math.tau / 10
        if math.sin(t * 6 + i) > 0:
            pygame.draw.circle(surface, (255, 210, 120),
                               (int(cx + math.cos(a) * r), int(cy + math.sin(a) * r)),
                               max(1, r // 16))


class CutsceneScene(Scene):
    PAGES: list = []
    PAGE_TIME = PAGE_TIME

    def __init__(self, app, slot: int = 0) -> None:
        super().__init__(app)
        self.slot = slot
        self.page = 0
        self.t = 0.0
        self._page_t = 0.0
        w, h = app.render_size
        self.bg = vertical_gradient(w, h, (4, 6, 16), (12, 10, 28))
        self.rng = random.Random(5)
        self.stars = [(self.rng.uniform(0, w), self.rng.uniform(0, h),
                       self.rng.choice((1, 1, 2)), self.rng.uniform(0, 6.28))
                      for _ in range(150)]

    # ------------------------------------------------------------------
    def on_enter(self) -> None:
        self.app.audio.start_music()

    def handle_event(self, event) -> None:
        if event.type != EventType.KEYDOWN:
            return
        if event.key in self.app.input.bindings.get("cancel", ()):
            self._finish()
        elif event.key in self.app.input.bindings.get("confirm", ()):
            self._advance()

    def _advance(self) -> None:
        if self.page < len(self.PAGES) - 1:
            self.page += 1
            self._page_t = 0.0
            self.app.audio.play("select")
        else:
            self._finish()

    def _finish(self) -> None:  # pragma: no cover - subclasses override
        raise NotImplementedError

    def update(self, dt: float) -> None:
        self.t += dt
        self._page_t += dt
        if self._page_t >= self.PAGE_TIME:
            self._advance()

    # ------------------------------------------------------------------
    def draw_bg(self, surface) -> None:
        pass

    def draw(self, surface: pygame.Surface) -> None:
        w, h = surface.get_size()
        surface.blit(self.bg, (0, 0))
        for sx, sy, r, ph in self.stars:
            tw = 0.5 + 0.5 * math.sin(self.t * 3 + ph)
            c = int(80 + 120 * tw)
            pygame.draw.circle(surface, (c, c, min(255, c + 20)), (int(sx), int(sy)), r)
        self.draw_bg(surface)

        title_key, lines = self.PAGES[self.page]
        panel = pygame.Rect(30, h - 122, w - 60, 100)
        draw_panel(surface, panel, fill=(6, 8, 18, 222), border=(90, 160, 210))
        draw_text(surface, self.app.fonts, i18n.t(title_key), (w // 2, panel.top + 14),
                  size=22, color=(120, 240, 255), center=True, bold=True)
        for i, key in enumerate(lines):
            draw_text(surface, self.app.fonts, i18n.t(key), (w // 2, panel.top + 40 + i * 19),
                      size=15, color=(210, 220, 235), center=True)
        draw_text(surface, self.app.fonts, i18n.t("cut.skip"), (w - 10, h - 12),
                  size=12, color=(110, 125, 150))
        dots = " ".join("●" if i == self.page else "○" for i in range(len(self.PAGES)))
        draw_text(surface, self.app.fonts, dots, (w // 2, h - 12), size=13,
                  color=(120, 170, 210), center=True)


class StoryCutScene(CutsceneScene):
    PAGES = [
        ("cut.story.1.title", ["cut.story.1.a", "cut.story.1.b"]),
        ("cut.story.2.title", ["cut.story.2.a", "cut.story.2.b"]),
        ("cut.story.3.title", ["cut.story.3.a", "cut.story.3.b"]),
    ]

    def draw_bg(self, surface) -> None:
        w, h = surface.get_size()
        _draw_station(surface, w - 120, h // 2 - 40, 40, self.t)

    def _finish(self) -> None:
        self.app.audio.play("confirm")
        self.app.switch_scene("cut_fly", slot=self.slot)


class FlyCutScene(CutsceneScene):
    PAGES = [
        ("cut.fly.1.title", ["cut.fly.1.a", "cut.fly.1.b"]),
        ("cut.fly.2.title", ["cut.fly.2.a", "cut.fly.2.b"]),
    ]

    def draw_bg(self, surface) -> None:
        w, h = surface.get_size()
        r = 10 + min(150, self.t * 16)
        _draw_station(surface, w // 2 + 40, h // 2 - 40, int(r), self.t)
        ship = art.flying_gunship_surface()
        sx = 30 + min(w * 0.55, self.t * 42)
        sy = h - 150 - min(70, self.t * 9)
        surface.blit(ship, (int(sx), int(sy)))

    def _finish(self) -> None:
        self.app.audio.play("confirm")
        self.app.switch_scene("play", room="station",
                              save=self.app.save.load(self.slot), slot=self.slot)


class EscapeCutScene(CutsceneScene):
    PAGES = [
        ("cut.escape.1.title", ["cut.escape.1.a", "cut.escape.1.b"]),
        ("cut.escape.2.title", ["cut.escape.2.a", "cut.escape.2.b"]),
    ]

    def draw_bg(self, surface) -> None:
        w, h = surface.get_size()
        cx, cy = 150, h // 2 - 40
        _draw_station(surface, cx, cy, 44, self.t, damaged=True)
        for i in range(4):
            rr = int(44 + (self.t * 70 + i * 46) % 230)
            pygame.draw.circle(surface, (255, 170, 90), (cx, cy), rr, 2)
            pygame.draw.circle(surface, (255, 90, 60), (cx, cy), max(1, rr - 6), 1)
        # ship fleeing to the right
        ship = art.flying_gunship_surface()
        sx = min(w - 130, 90 + self.t * 95)
        surface.blit(ship, (int(sx), h - 124))

    def _finish(self) -> None:
        self.app.audio.stop_music()
        self.app.audio.play("upgrade")
        self.app.switch_scene("end", win=True, stats={"station": True})
