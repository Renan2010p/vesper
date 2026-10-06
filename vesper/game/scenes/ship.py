"""Boarding the gunship: refuel and optionally save."""

from __future__ import annotations

import pygame

from vesper.engine.platform import EventType
from vesper.engine.scene import Scene
from vesper.engine.ui import draw_panel, draw_text

from ..components import Health, Loadout
from ..i18n import t


class ShipScene(Scene):
    def __init__(self, app, play) -> None:
        super().__init__(app)
        self.play = play
        self.index = 0
        self.saved = False
        self.menu = [("save", t("ship.save")), ("depart", t("ship.depart")),
                     ("leave", t("ship.leave"))]

    def on_enter(self) -> None:
        player = self.play.world.first(tag="player")
        if player is not None:
            health: Health = player.get(Health)
            loadout: Loadout = player.get(Loadout)
            health.hp = health.max_hp
            loadout.missiles = loadout.max_missiles
        self.app.audio.play("upgrade")
        self.play.hud.add_toast(t("toast.energy"), t("toast.energy_sub"), "save")

    # ------------------------------------------------------------------
    def handle_event(self, event) -> None:
        if event.type != EventType.KEYDOWN:
            return
        down = self.app.input.bindings.get("down", ())
        up = self.app.input.bindings.get("up", ())
        confirm = self.app.input.bindings.get("confirm", ())
        cancel = self.app.input.bindings.get("cancel", ())
        pause = self.app.input.bindings.get("pause", ())
        if event.key in down:
            self.index = (self.index + 1) % len(self.menu)
            self.app.audio.play("select")
        elif event.key in up:
            self.index = (self.index - 1) % len(self.menu)
            self.app.audio.play("select")
        elif event.key in confirm:
            self._activate(self.menu[self.index][0])
        elif event.key in cancel or event.key in pause:
            self._leave()

    def _activate(self, action: str) -> None:
        if action == "save":
            self.app.audio.play("confirm")
            player = self.play.world.first(tag="player")
            self.play._save_game(player)
            self.saved = True
            self.play.hud.add_toast(t("toast.mission_saved"),
                                   t("toast.mission_saved_sub"), "save")
            self.menu = [("depart", t("ship.depart")), ("leave", t("ship.leave"))]
            self.index = 0
        elif action == "depart":
            self.app.audio.play("confirm")
            player = self.play.world.first(tag="player")
            self.play._save_game(player)
            self.app.switch_scene("cut_story", slot=self.play.slot)
        else:
            self._leave()

    def _leave(self) -> None:
        self.app.audio.play("cancel")
        self.app.scenes.set_current(self.play)

    # ------------------------------------------------------------------
    def draw(self, surface: pygame.Surface) -> None:
        self.play.draw(surface)
        overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        overlay.fill((4, 6, 12, 180))
        surface.blit(overlay, (0, 0))

        w, h = surface.get_size()
        panel = pygame.Rect(w // 2 - 150, h // 2 - 92, 300, 184)
        draw_panel(surface, panel, fill=(10, 14, 24, 235), border=(90, 240, 255))
        draw_text(surface, self.app.fonts, t("ship.title"), (w // 2, panel.top + 26),
                  size=30, color=(120, 240, 255), center=True, bold=True)
        status = t("ship.saved") if self.saved else t("ship.restored")
        draw_text(surface, self.app.fonts, status, (w // 2, panel.top + 56), size=17,
                  color=(180, 220, 200), center=True)
        draw_text(surface, self.app.fonts, t("ship.save_q"), (w // 2, panel.top + 80),
                  size=16, color=(200, 215, 235), center=True)

        start = panel.top + 112
        for i, (action, label) in enumerate(self.menu):
            selected = i == self.index
            color = (255, 240, 170) if selected else (150, 165, 190)
            text = f"» {label}" if selected else label
            draw_text(surface, self.app.fonts, text, (w // 2, start + i * 28),
                      size=22, color=color, center=True, bold=selected)
        draw_text(surface, self.app.fonts, t("ship.hint"), (w // 2, panel.bottom + 16),
                  size=14, color=(130, 150, 180), center=True)
