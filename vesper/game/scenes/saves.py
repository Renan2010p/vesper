"""Save-file select — a Super-Metroid-style screen with three slots.

Each slot shows the area name, play time and completion.  Enter starts a new
game (empty slot) or continues (occupied slot); ``V`` arms erase, Esc goes back.
"""

from __future__ import annotations

import math

import pygame

from vesper.engine.platform import EventType
from vesper.engine.scene import Scene
from vesper.engine.sprites import vertical_gradient
from vesper.engine.ui import draw_panel, draw_text

from .. import art, i18n
from ..config import ABILITY_ORDER, CORE_GOAL
from ..rooms import ROOMS

SLOTS = 3
CARD_H = 58


def _area_label(room_id: str) -> str:
    spec = ROOMS.get(room_id)
    if spec is not None:
        return i18n.t(spec["label"])
    return i18n.t("zone." + room_id) if room_id else "?"


class SaveSelectScene(Scene):
    def __init__(self, app) -> None:
        super().__init__(app)
        self.t = 0.0
        self.index = 0
        self.erase = False
        self.saves = [app.save.load(i) for i in range(SLOTS)]
        self.bg = vertical_gradient(app.render_size[0], app.render_size[1],
                                    (6, 8, 20), (18, 10, 30))
        self.hero = pygame.transform.scale(art._hunter("side", leg=0), (64, 88))

    def on_enter(self) -> None:
        self.app.audio.start_music()

    # ------------------------------------------------------------------
    # input
    # ------------------------------------------------------------------
    def handle_event(self, event) -> None:
        if event.type != EventType.KEYDOWN:
            return
        down = self.app.input.bindings.get("down", ())
        up = self.app.input.bindings.get("up", ())
        confirm = self.app.input.bindings.get("confirm", ())
        cancel = self.app.input.bindings.get("cancel", ())
        erase_key = self.app.input.bindings.get("ability", ())
        if event.key in down:
            self.index = (self.index + 1) % SLOTS
            self.app.audio.play("select")
        elif event.key in up:
            self.index = (self.index - 1) % SLOTS
            self.app.audio.play("select")
        elif event.key in confirm:
            self._confirm()
        elif event.key in erase_key:
            if self.saves[self.index] is not None:
                self.erase = not self.erase
                self.app.audio.play("select")
        elif event.key in cancel:
            if self.erase:
                self.erase = False
            else:
                self.app.switch_scene("title")

    def _confirm(self) -> None:
        save = self.saves[self.index]
        if self.erase:
            if save is not None:
                self.app.save.delete(self.index)
                self.saves[self.index] = None
                self.app.audio.play("enemy_die")
            self.erase = False
            return
        self.app.audio.play("confirm")
        if save is None:
            self.app.switch_scene("intro", slot=self.index)
        else:
            self.app.switch_scene("play", save=save, slot=self.index)

    def update(self, dt: float) -> None:
        self.t += dt

    # ------------------------------------------------------------------
    # drawing
    # ------------------------------------------------------------------
    def _right(self, surface, text, right, y, size, color, bold=False) -> None:
        font = self.app.fonts.get(size, bold)
        width = font.size(text)[0] if font is not None else 0
        draw_text(surface, self.app.fonts, text, (right - width, y), size=size,
                  color=color, bold=bold)

    def draw(self, surface: pygame.Surface) -> None:
        surface.blit(self.bg, (0, 0))
        w = surface.get_width()
        draw_text(surface, self.app.fonts, i18n.t("save.title"), (w // 2, 18),
                  size=28, color=(120, 240, 255), center=True, bold=True)

        card_x, card_w = 24, w - 190
        for i in range(SLOTS):
            self._draw_card(surface, i, card_x, 44 + i * 62, card_w, CARD_H)
        self._draw_preview(surface, w - 158, 44, 134, 200)
        self._draw_footer(surface, w)

    def _draw_card(self, surface, i, x, y, w, h) -> None:
        selected = i == self.index
        save = self.saves[i]
        erasing = selected and self.erase and save is not None
        border = (255, 110, 110) if erasing else ((120, 245, 255) if selected else (70, 90, 120))
        draw_panel(surface, pygame.Rect(x, y, w, h),
                   fill=(18, 24, 38, 238) if selected else (12, 16, 26, 220),
                   border=border)

        label = f"{'» ' if selected else ''}{i18n.t('save.file', n=i + 1)}"
        draw_text(surface, self.app.fonts, label, (x + 14, y + 8), size=18,
                  color=(255, 240, 170) if selected else (150, 165, 190), bold=selected)
        if save is None:
            self._right(surface, i18n.t("save.empty"), x + w - 14, y + 12, 16,
                        (110, 125, 150))
            return

        mm, ss = divmod(int(save.play_time), 60)
        info = i18n.t("save.info", time=f"{mm:02d}:{ss:02d}",
                      a=len(save.abilities), b=len(ABILITY_ORDER),
                      c=int(save.flags.get("cores", 0)), d=CORE_GOAL)
        self._right(surface, info, x + w - 14, y + 11, 13, (150, 185, 210))
        draw_text(surface, self.app.fonts, _area_label(save.spawn_zone), (x + 14, y + 31),
                  size=15, color=(190, 210, 235))

    def _draw_preview(self, surface, x, y, w, h) -> None:
        draw_panel(surface, pygame.Rect(x, y, w, h), fill=(10, 14, 26, 235),
                   border=(90, 160, 210))
        save = self.saves[self.index]
        bob = math.sin(self.t * 2) * 2
        surface.blit(self.hero, (x + w // 2 - self.hero.get_width() // 2,
                                 y + 16 + bob))
        cx = x + w // 2
        yy = y + 116
        if save is None:
            draw_text(surface, self.app.fonts, i18n.t("save.new"), (cx, yy + 10),
                      size=16, color=(150, 240, 190), center=True, bold=True)
            return
        draw_text(surface, self.app.fonts, _area_label(save.spawn_zone),
                  (cx, yy), size=14, color=(200, 220, 240), center=True)
        mm, ss = divmod(int(save.play_time), 60)
        draw_text(surface, self.app.fonts, i18n.t("save.time", time=f"{mm:02d}:{ss:02d}"),
                  (cx, yy + 22), size=15, color=(150, 200, 225), center=True)
        draw_text(surface, self.app.fonts, i18n.t("save.energy",
                  hp=int(save.health), hp_max=int(save.max_health)),
                  (cx, yy + 42), size=13, color=(160, 200, 180), center=True)
        draw_text(surface, self.app.fonts, i18n.t("save.missiles",
                  n=int(save.missiles), n_max=int(save.max_missiles)),
                  (cx, yy + 60), size=13, color=(220, 190, 150), center=True)
        action = i18n.t("save.erase_action") if self.erase else i18n.t("menu.continue")
        color = (255, 140, 140) if self.erase else (255, 240, 170)
        draw_text(surface, self.app.fonts, action, (cx, y + h - 22),
                  size=14, color=color, center=True, bold=True)

    def _draw_footer(self, surface, w) -> None:
        if self.erase:
            draw_text(surface, self.app.fonts, i18n.t("save.erase_q", n=self.index + 1),
                      (w // 2, 252), size=18, color=(255, 130, 130),
                      center=True, bold=True)
            draw_text(surface, self.app.fonts, i18n.t("save.hint_confirm"),
                      (w // 2, 273), size=13, color=(180, 150, 150), center=True)
        else:
            draw_text(surface, self.app.fonts, i18n.t("save.footer"),
                      (w // 2, 272), size=14, color=(130, 150, 180), center=True)
