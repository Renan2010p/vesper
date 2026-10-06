"""Opening story + ship descent into the Nara surface.

Flow: title -> intro -> play.  The intro shows original lore pages while Vesper's
gunship descends through the storm onto the middle of the surface.
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

PAGES = [
    ("intro.1.title", ["intro.1.1", "intro.1.2"]),
    ("intro.2.title", ["intro.2.1", "intro.2.2", "intro.2.3"]),
    ("intro.3.title", ["intro.3.1", "intro.3.2"]),
    ("intro.4.title", ["intro.4.1", "intro.4.2", "intro.4.3"]),
]


class IntroScene(Scene):
    def __init__(self, app, slot: int = 0) -> None:
        super().__init__(app)
        self.slot = slot
        self.page = 0
        self.t = 0.0
        self.done_descent = False
        w, h = app.render_size
        self.bg = vertical_gradient(w, h, (6, 8, 18), (28, 30, 46))
        rng = random.Random(21)
        self.stars = [(rng.uniform(0, w), rng.uniform(0, h * 0.7),
                       rng.choice((1, 1, 2)), rng.uniform(0.0, 6.28)) for _ in range(140)]
        self.ship = art.flying_gunship_surface()
        self.horizon = h - 54
        self.ground = vertical_gradient(w, h - self.horizon + 10, (40, 44, 58), (16, 18, 26))

    def on_enter(self) -> None:
        self.app.audio.start_music()

    # ------------------------------------------------------------------
    def handle_event(self, event) -> None:
        if event.type != EventType.KEYDOWN:
            return
        confirm = self.app.input.bindings.get("confirm", ())
        cancel = self.app.input.bindings.get("cancel", ())
        if event.key in cancel:
            self._finish()
        elif event.key in confirm:
            if self.page < len(PAGES) - 1:
                self.page += 1
                self.app.audio.play("select")
            else:
                self._finish()

    def _finish(self) -> None:
        self.app.audio.play("confirm")
        self.app.switch_scene("play", slot=self.slot)

    # ------------------------------------------------------------------
    def update(self, dt: float) -> None:
        self.t += dt
        if self.t >= 6.0:
            self.done_descent = True

    # -- ship fly-by ------------------------------------------------------
    T_FLY = 2.4
    T_DESC = 2.6

    def _ship_pose(self):
        """Return the gunship's (centre_x, centre_y, angle_deg) at this time."""
        w, _h = self.app.render_size
        sw = self.ship.get_width()
        target_y = self.horizon - 24
        cx = w // 2
        if self.t < self.T_FLY:                          # fly in from the left
            u = self.t / self.T_FLY
            e = 1 - (1 - u) ** 2
            x = -sw + (cx + sw) * e
            y = 150 + math.sin(u * math.pi) * 8
            angle = 0.0
        elif self.t < self.T_FLY + self.T_DESC:          # curve down and flare
            u = (self.t - self.T_FLY) / self.T_DESC
            e = u * u
            x = cx + math.sin(u * math.pi) * 6
            y = 150 + (target_y - 150) * e
            angle = -52.0 * math.sin(u * math.pi)
        else:                                            # rest on the ground
            x, y, angle = cx, target_y, 0.0
        return x, y, angle

    def _draw_ship(self, surface, x, y, angle) -> None:
        glow = pygame.Surface((96, 44), pygame.SRCALPHA)
        for r in range(32, 3, -5):
            a = int(90 * (1 - r / 32))
            pygame.draw.ellipse(glow, (120, 200, 255, a), (48 - r, 22 - r // 2, r * 2, r))
        surface.blit(glow, (x - 48, y - 22))

        if self.t < self.T_FLY:                           # horizontal speed lines
            for i, dy in enumerate((-9, 0, 9)):
                ln = 26 + i * 7
                pygame.draw.line(surface, (120, 160, 210),
                                 (x - 44, y + dy), (x - 44 - ln, y + dy), 2)
        elif self.t < self.T_FLY + self.T_DESC:           # descent speed lines
            for i, dx in enumerate((-11, 0, 11)):
                ln = 22 + i * 7
                pygame.draw.line(surface, (120, 160, 210),
                                 (x + dx, y - 30), (x + dx, y - 30 - ln), 2)

        img = pygame.transform.rotate(self.ship, angle)
        surface.blit(img, img.get_rect(center=(int(x), int(y))))

    def draw(self, surface: pygame.Surface) -> None:
        w, h = surface.get_size()
        surface.blit(self.bg, (0, 0))

        # stars
        for (sx, sy, r, phase) in self.stars:
            tw = 0.5 + 0.5 * math.sin(self.t * 3 + phase)
            c = int(90 + 120 * tw)
            pygame.draw.circle(surface, (c, c, min(255, c + 20)),
                               (int(sx), int(sy)), r)

        # the Nara planet orbits a black hole
        art.draw_black_hole(surface, w - 150, 92, 56, self.t)

        # planet horizon
        pygame.draw.circle(surface, (34, 38, 52), (w // 2, h + 900), 952)
        surface.blit(self.ground, (0, self.horizon))

        # rain near the surface
        for i in range(120):
            x = (i * 53 + int(self.t * 520)) % (w + 60) - 30
            y = self.horizon - 40 + (i * 37 + int(self.t * 900)) % 90
            pygame.draw.line(surface, (110, 130, 165), (x, y), (x - 5, y + 14), 1)

        # the gunship flies in, curves down and lands (Samus-style fly-by)
        ship_x, ship_y, angle = self._ship_pose()
        self._draw_ship(surface, ship_x, ship_y, angle)

        # text panel
        title_key, line_keys = PAGES[self.page]
        panel = pygame.Rect(40, 24, w - 80, 116)
        draw_panel(surface, panel, fill=(8, 10, 20, 210), border=(90, 160, 210))
        draw_text(surface, self.app.fonts, i18n.t(title_key), (w // 2, 44), size=26,
                  color=(120, 240, 255), center=True, bold=True)
        for i, key in enumerate(line_keys):
            draw_text(surface, self.app.fonts, i18n.t(key), (w // 2, 78 + i * 20),
                      size=16, color=(210, 220, 235), center=True)

        if self.page < len(PAGES) - 1:
            prompt = i18n.t("intro.prompt_next")
        else:
            prompt = i18n.t("intro.prompt_land")
        highlight = self.done_descent and self.page == len(PAGES) - 1
        if highlight:
            blink = (math.sin(self.t * 6) > -0.3)
            if blink:
                draw_text(surface, self.app.fonts, prompt, (w // 2, h - 24), size=17,
                          color=(255, 240, 170), center=True, bold=True)
        else:
            draw_text(surface, self.app.fonts, prompt, (w // 2, h - 24), size=16,
                      color=(150, 165, 190), center=True)
