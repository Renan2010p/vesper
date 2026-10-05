"""Pause overlay scene."""

from __future__ import annotations

import pygame

from vesper.engine.platform import EventType, Key
from vesper.engine.scene import Scene
from vesper.engine.ui import draw_panel, draw_text

from .. import i18n, set_language
from ..hud import draw_room_map


class PauseScene(Scene):
    def __init__(self, app, play) -> None:
        super().__init__(app)
        self.play = play
        self.show_map = False
        self.entries = self._build_entries()
        self.index = 0

    def _build_entries(self):
        sound = i18n.t("on") if self.app.audio.enabled else i18n.t("off")
        lang = i18n.t("lang." + i18n.get_locale())
        return [
            ("resume", i18n.t("pause.resume")),
            ("map", i18n.t("pause.map")),
            ("sound", f"{i18n.t('pause.sound')}: {sound}"),
            ("language", f"{i18n.t('pause.language')}: {lang}"),
            ("abort", i18n.t("pause.abort")),
        ]

    def on_enter(self) -> None:
        self.index = 0
        self.show_map = False
        self.entries = self._build_entries()

    def handle_event(self, event) -> None:
        if event.type != EventType.KEYDOWN:
            return
        down = self.app.input.bindings.get("down", ())
        up = self.app.input.bindings.get("up", ())
        confirm = self.app.input.bindings.get("confirm", ())
        pause = self.app.input.bindings.get("pause", ())
        cancel = self.app.input.bindings.get("cancel", ())
        if event.key in down:
            self.index = (self.index + 1) % len(self.entries)
            self.app.audio.play("select")
        elif event.key in up:
            self.index = (self.index - 1) % len(self.entries)
            self.app.audio.play("select")
        elif event.key in confirm:
            self._activate(self.entries[self.index][0])
        elif event.key in cancel or event.key == Key.TAB:
            self.show_map = not self.show_map
        elif event.key in pause:
            self._resume()

    def _activate(self, action: str) -> None:
        self.app.audio.play("confirm")
        if action == "resume":
            self._resume()
        elif action == "map":
            self.show_map = not self.show_map
        elif action == "sound":
            self.app.audio.set_enabled(not self.app.audio.enabled)
            self.entries = self._build_entries()
        elif action == "language":
            set_language(self.app, i18n.next_locale())
            self.entries = self._build_entries()
        elif action == "abort":
            self.app.switch_scene("title")

    def _resume(self) -> None:
        self.app.scenes.set_current(self.play)

    def draw(self, surface: pygame.Surface) -> None:
        self.play.draw(surface)
        overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        overlay.fill((4, 6, 12, 190))
        surface.blit(overlay, (0, 0))

        draw_text(surface, self.app.fonts, i18n.t("pause.title"), (256, 34), size=36,
                  color=(120, 240, 255), center=True, bold=True)

        if self.show_map:
            draw_room_map(surface, self.play.world, self.app.fonts)
        else:
            panel = pygame.Rect(156, 78, 200, 176)
            draw_panel(surface, panel)
            start = 108
            for i, (action, label) in enumerate(self.entries):
                selected = i == self.index
                color = (255, 240, 170) if selected else (150, 165, 190)
                text = f"» {label}" if selected else label
                draw_text(surface, self.app.fonts, text, (256, start + i * 28),
                          size=20, color=color, center=True, bold=selected)

        draw_text(surface, self.app.fonts, i18n.t("pause.hint"), (256, 272), size=15,
                  color=(130, 150, 180), center=True)
