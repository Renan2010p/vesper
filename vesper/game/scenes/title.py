"""Title screen."""

from __future__ import annotations

import math
import random

import pygame

from vesper.engine.platform import EventType
from vesper.engine.scene import Scene
from vesper.engine.sprites import vertical_gradient
from vesper.engine.ui import draw_text

from .. import art, i18n, set_language


class TitleScene(Scene):
    def __init__(self, app) -> None:
        super().__init__(app)
        self.t = 0.0
        self.index = 0
        self.entries = self._build_entries()
        self.bg = vertical_gradient(app.render_size[0], app.render_size[1],
                                    (8, 10, 22), (24, 14, 34))
        rng = random.Random(3)
        self.stars = [(rng.uniform(0, 512), rng.uniform(0, 288),
                       rng.choice((60, 90, 130)), rng.choice((1, 1, 2)))
                      for _ in range(120)]
        self.hero = pygame.transform.scale(art._hunter("side", leg=0), (72, 96))

    def _build_entries(self):
        entries = [("new", i18n.t("menu.new"))]
        sound = i18n.t("on") if self.app.audio.enabled else i18n.t("off")
        entries.append(("sound", f"{i18n.t('menu.sound')}: {sound}"))
        lang = i18n.t("lang." + i18n.get_locale())
        entries.append(("language", f"{i18n.t('menu.language')}: {lang}"))
        entries.append(("quit", i18n.t("menu.quit")))
        return entries

    def on_enter(self) -> None:
        self.entries = self._build_entries()
        self.index = min(self.index, len(self.entries) - 1)
        self.app.audio.start_music()

    # ------------------------------------------------------------------
    def handle_event(self, event) -> None:
        if event.type != EventType.KEYDOWN:
            return
        down = self.app.input.bindings.get("down", ())
        up = self.app.input.bindings.get("up", ())
        confirm = self.app.input.bindings.get("confirm", ())
        if event.key in down:
            self.index = (self.index + 1) % len(self.entries)
            self.app.audio.play("select")
        elif event.key in up:
            self.index = (self.index - 1) % len(self.entries)
            self.app.audio.play("select")
        elif event.key in confirm:
            self._activate(self.entries[self.index][0])

    def _activate(self, action: str) -> None:
        self.app.audio.play("confirm")
        if action == "new":
            self.app.switch_scene("saves")
        elif action == "sound":
            self.app.audio.set_enabled(not self.app.audio.enabled)
            self.entries = self._build_entries()
        elif action == "language":
            set_language(self.app, i18n.next_locale())
            self.entries = self._build_entries()
        elif action == "quit":
            self.app.quit()

    # ------------------------------------------------------------------
    def update(self, dt: float) -> None:
        self.t += dt

    def draw(self, surface: pygame.Surface) -> None:
        surface.blit(self.bg, (0, 0))
        for sx, sy, color, r in self.stars:
            x = (sx - self.t * 6) % 512
            y = (sy - self.t * 3) % 288
            pygame.draw.circle(surface, color, (int(x), int(y)), r)

        bob = math.sin(self.t * 2) * 4
        surface.blit(self.hero, (74, 120 + bob))

        draw_text(surface, self.app.fonts, "VESPER", (300, 56), size=64,
                  color=(120, 240, 255), center=True, bold=True)
        draw_text(surface, self.app.fonts, i18n.t("title.subtitle"), (300, 96),
                  size=22, color=(200, 170, 220), center=True)

        start = 140
        for i, (action, label) in enumerate(self.entries):
            selected = i == self.index
            color = (255, 240, 170) if selected else (140, 155, 180)
            text = f"» {label}" if selected else label
            draw_text(surface, self.app.fonts, text, (300, start + i * 28), size=22,
                      color=color, center=True, bold=selected)

        draw_text(surface, self.app.fonts, i18n.t("title.controls"), (256, 272),
                  size=15, color=(120, 140, 170), center=True)
        draw_text(surface, self.app.fonts,
                  f"{i18n.t('title.license')}  •  {i18n.t('title.studio')}",
                  (256, 284), size=13, color=(90, 105, 130), center=True)
