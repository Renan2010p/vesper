"""Opening story + ship fly-by into the Nara surface.

Flow: title -> intro -> play.  Original lore pages are shown over a living
storm: drifting clouds, lightning, meteors, rain, and Vesper's gunship flying
in and landing.
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
    T_FLY = 2.4
    T_DESC = 2.6

    def __init__(self, app, slot: int = 0) -> None:
        super().__init__(app)
        self.slot = slot
        self.page = 0
        self.t = 0.0
        self.done_descent = False
        w, h = app.render_size
        self.bg = vertical_gradient(w, h, (6, 8, 18), (28, 30, 46))
        self.rng = random.Random(21)
        self.stars = [(self.rng.uniform(0, w), self.rng.uniform(0, h * 0.7),
                       self.rng.choice((1, 1, 2)), self.rng.uniform(0.0, 6.28))
                      for _ in range(140)]
        self.ship = art.flying_gunship_surface()
        self.horizon = h - 54
        self.ground = vertical_gradient(w, h - self.horizon + 10, (40, 44, 58), (16, 18, 26))

        # weather state
        self.flash = 0.0
        self.bolt_pts = []
        self._next_bolt = 1.0
        self.meteor = None
        self._next_meteor = 1.5
        self.land_t = None

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

        # lightning
        self.flash = max(0.0, self.flash - dt * 3.3)
        if self.t >= self._next_bolt:
            self.flash = 1.0
            self.bolt_pts = self._make_bolt(self.rng.randint(50, self.app.render_size[0] - 50))
            self._next_bolt = self.t + self.rng.uniform(1.3, 2.8)

        # shooting stars
        if self.t >= self._next_meteor:
            w = self.app.render_size[0]
            self.meteor = [self.rng.uniform(0, w), self.rng.uniform(-10, 40),
                           self.rng.uniform(170, 260), self.rng.uniform(70, 120), 0.9]
            self._next_meteor = self.t + self.rng.uniform(2.4, 5.0)
        if self.meteor is not None:
            self.meteor[0] += self.meteor[2] * dt
            self.meteor[1] += self.meteor[3] * dt
            self.meteor[4] -= dt
            if self.meteor[4] <= 0 or self.meteor[0] > self.app.render_size[0] + 40:
                self.meteor = None

        # touchdown -> landing dust
        if self.t >= self.T_FLY + self.T_DESC and self.land_t is None:
            self.land_t = self.t
            self.app.audio.play("land")

    def _make_bolt(self, x):
        pts = [(x, 6)]
        y = 6
        while y < self.horizon - 14:
            x += self.rng.choice((-16, -9, 9, 16))
            y += self.rng.randint(11, 20)
            pts.append((x, y))
        return pts

    # ------------------------------------------------------------------
    # ship
    # ------------------------------------------------------------------
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
        thrust = 1.0 if self.t < self.T_FLY + self.T_DESC else 0.32
        flicker = (0.7 + 0.3 * math.sin(self.t * 42.0)) * thrust
        glow = pygame.Surface((96, 44), pygame.SRCALPHA)
        for r in range(32, 3, -5):
            a = int(90 * (1 - r / 32) * flicker)
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

    # ------------------------------------------------------------------
    # sky
    # ------------------------------------------------------------------
    def _draw_stars(self, surface) -> None:
        for (sx, sy, r, phase) in self.stars:
            tw = 0.5 + 0.5 * math.sin(self.t * 3 + phase)
            c = int(90 + 120 * tw)
            pygame.draw.circle(surface, (c, c, min(255, c + 20)), (int(sx), int(sy)), r)

    def _draw_meteors(self, surface) -> None:
        if self.meteor is None:
            return
        x, y, vx, vy, _life = self.meteor
        pygame.draw.line(surface, (200, 220, 255), (x, y), (x - vx * 0.09, y - vy * 0.09), 2)
        pygame.draw.circle(surface, (255, 255, 255), (int(x), int(y)), 1)

    def _draw_clouds(self, surface, w) -> None:
        layer = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        for speed, alpha, ybase, cw in ((7, 55, 148, 170), (15, 80, 174, 118)):
            x = -int(self.t * speed) % (cw * 2) - cw * 2
            while x < w + cw:
                pygame.draw.ellipse(layer, (18, 20, 34, alpha), (x, ybase, cw, 34))
                pygame.draw.ellipse(layer, (18, 20, 34, alpha),
                                    (x + cw * 0.42, ybase - 8, cw * 0.8, 26))
                x += cw * 2
        surface.blit(layer, (0, 0))

    def _draw_lightning(self, surface, w) -> None:
        if self.flash <= 0:
            return
        overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        overlay.fill((200, 216, 255, int(120 * self.flash)))
        surface.blit(overlay, (0, 0))
        if self.flash > 0.4 and self.bolt_pts:
            pygame.draw.lines(surface, (238, 242, 255), False, self.bolt_pts, 2)
            pygame.draw.lines(surface, (150, 190, 255), False, self.bolt_pts, 1)

    def _draw_rain(self, surface, w) -> None:
        for i in range(120):
            x = (i * 53 + int(self.t * 520)) % (w + 60) - 30
            y = self.horizon - 40 + (i * 37 + int(self.t * 900)) % 90
            pygame.draw.line(surface, (110, 130, 165), (x, y), (x - 5, y + 14), 1)

    def _draw_landing_dust(self, surface, w) -> None:
        if self.land_t is None:
            return
        u = self.t - self.land_t
        if u > 1.3:
            return
        p = u / 1.3
        layer = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        y = self.horizon + 2
        for dx, rw in ((-72, 70), (72, 70), (-112, 46), (112, 46)):
            r = int(rw * (0.3 + p))
            a = int(110 * (1 - p))
            pygame.draw.ellipse(layer, (150, 162, 188, a),
                                (w // 2 + dx - r // 2, y - 7, r, 14))
        surface.blit(layer, (0, 0))

    # ------------------------------------------------------------------
    def draw(self, surface: pygame.Surface) -> None:
        w, h = surface.get_size()
        surface.blit(self.bg, (0, 0))
        self._draw_stars(surface)
        self._draw_meteors(surface)

        # the Nara planet orbits a black hole
        art.draw_black_hole(surface, w - 150, 92, 56, self.t)
        self._draw_clouds(surface, w)

        # planet horizon
        pygame.draw.circle(surface, (34, 38, 52), (w // 2, h + 900), 952)
        surface.blit(self.ground, (0, self.horizon))
        self._draw_lightning(surface, w)
        self._draw_rain(surface, w)
        self._draw_landing_dust(surface, w)

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
