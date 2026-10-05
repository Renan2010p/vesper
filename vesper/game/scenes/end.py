"""End-of-game scene (victory or defeat)."""

from __future__ import annotations

import math
import random

import pygame

from vesper.engine.platform import EventType
from vesper.engine.scene import Scene
from vesper.engine.sprites import vertical_gradient
from vesper.engine.ui import draw_text

from .. import art, i18n


class EndScene(Scene):
    def __init__(self, app, win: bool = True, stats: dict | None = None) -> None:
        super().__init__(app)
        self.win = win
        self.stats = stats or {}
        self.t = 0.0
        self.bg = vertical_gradient(app.render_size[0], app.render_size[1],
                                    (8, 20, 26), (14, 8, 30))
        rng = random.Random(11)
        self.sparks = [(rng.uniform(0, 512), rng.uniform(0, 288),
                        rng.uniform(0.5, 1.5)) for _ in range(80)]
        self.hero = pygame.transform.scale(art._hunter("side", leg=0), (54, 72))

    def on_enter(self) -> None:
        self.app.audio.stop_music()
        self.app.audio.play("upgrade")

    def handle_event(self, event) -> None:
        if event.type != EventType.KEYDOWN:
            return
        if event.key in self.app.input.bindings.get("confirm", ()) or \
                event.key in self.app.input.bindings.get("pause", ()):
            self.app.switch_scene("title")

    def update(self, dt: float) -> None:
        self.t += dt

    def draw(self, surface: pygame.Surface) -> None:
        surface.blit(self.bg, (0, 0))
        for sx, sy, spd in self.sparks:
            x = (sx + self.t * 10 * spd) % 512
            y = (sy - self.t * 20 * spd) % 288
            pygame.draw.circle(surface, (120, 220, 255), (int(x), int(y)), 1)

        bob = math.sin(self.t * 2) * 3
        surface.blit(self.hero, (229, 150 + bob))

        title = i18n.t("end.win") if self.win else i18n.t("end.lose")
        color = (120, 250, 200) if self.win else (250, 120, 130)
        draw_text(surface, self.app.fonts, title, (256, 70), size=44,
                  color=color, center=True, bold=True)
        draw_text(surface, self.app.fonts, i18n.t("end.win_line"), (256, 106),
                  size=18, color=(200, 210, 230), center=True)

        seconds = int(self.stats.get("time", 0))
        mins, secs = divmod(seconds, 60)
        draw_text(surface, self.app.fonts, i18n.t("end.time", mm=mins, ss=secs),
                  (256, 232), size=18, color=(180, 200, 220), center=True)
        draw_text(surface, self.app.fonts, i18n.t("end.return"), (256, 262),
                  size=18, color=(150, 170, 195), center=True)
