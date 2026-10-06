"""Heads-up display, toasts and the minimap."""

from __future__ import annotations

import math
import random
from dataclasses import dataclass
from typing import List

import pygame

from vesper.engine.physics import Transform
from vesper.engine.ui import Fonts, draw_bar, draw_text

from . import art
from .components import Boss, Health, Loadout, Nametag, Player
from .config import CORE_GOAL
from .i18n import t


@dataclass
class Toast:
    title: str
    subtitle: str
    kind: str
    timer: float = 3.4
    total: float = 3.4


class HUD:
    def __init__(self) -> None:
        self.toasts: List[Toast] = []
        self.boss_ref = None
        self._missile_icon = art.missile_icon(16)
        self._shake = 0.0
        self._shake_time = 0.0
        self._offset = (0, 0)
        self._layer = None

    def add_toast(self, title: str, subtitle: str = "", kind: str = "item") -> None:
        self.toasts.append(Toast(title, subtitle, kind))
        if len(self.toasts) > 4:
            self.toasts.pop(0)

    def shake(self, magnitude: float = 9.0, duration: float = 0.32) -> None:
        """Jolt the whole HUD as if her suit panel absorbed a hit."""
        self._shake = max(self._shake, magnitude)
        self._shake_time = max(self._shake_time, duration)

    def update(self, dt: float) -> None:
        for toast in self.toasts:
            toast.timer -= dt
        self.toasts = [t for t in self.toasts if t.timer > 0]

        if self._shake_time > 0:
            self._shake_time -= dt
            if self._shake_time <= 0:
                self._shake = 0.0
        if self._shake > 0:
            m = int(self._shake)
            self._offset = (random.randint(-m, m), random.randint(-m, m))
        else:
            self._offset = (0, 0)

    # -- drawing ----------------------------------------------------------
    def draw(self, surface: pygame.Surface, world, fonts: Fonts) -> None:
        layer = self._layer
        if layer is None or layer.get_size() != surface.get_size():
            layer = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
            self._layer = layer
        layer.fill((0, 0, 0, 0))
        self._draw_hud(layer, world, fonts)
        surface.blit(layer, self._offset)

    def _draw_hud(self, surface: pygame.Surface, world, fonts: Fonts) -> None:
        player = world.first(tag="player")
        if player is not None:
            health: Health = player.get(Health)
            loadout: Loadout = player.get(Loadout)
            self._draw_bar(surface, world, fonts, player, health, loadout)
        self._draw_boss(surface, world, fonts)
        countdown = world.services.get("countdown")
        if countdown is not None:
            self._draw_countdown(surface, fonts, countdown)
        self._draw_toasts(surface, fonts, 96 if countdown is not None else 52)

    def _draw_bar(self, surface, world, fonts, player, health: Health,
                  loadout: Loadout) -> None:
        """Top status bar: ENERGY, missiles, cores and a corner minimap."""
        width = surface.get_width()
        bar_h = 42
        panel = pygame.Surface((width, bar_h), pygame.SRCALPHA)
        panel.fill((6, 8, 16, 215))
        surface.blit(panel, (0, 0))
        pygame.draw.line(surface, (70, 96, 130), (0, bar_h - 1), (width, bar_h - 1), 2)

        # ENERGY ----------------------------------------------------------
        draw_text(surface, fonts, t("hud.vitals"), (10, 5), size=14,
                  color=(150, 190, 220))
        ratio = 0.0 if health.max_hp <= 0 else health.hp / health.max_hp
        if ratio > 0.5:
            color = (110, 235, 140)
        elif ratio > 0.25:
            color = (245, 210, 110)
        else:
            color = (245, 100, 100)
        draw_bar(surface, 10, 21, 150, 12, ratio, color, segments=12)
        draw_text(surface, fonts, str(int(health.hp)), (166, 17), size=18,
                  color=(235, 245, 255))

        # charge gauge (appears under the energy bar while charging) -------
        pcomp: Player | None = player.get(Player)
        if pcomp is not None and pcomp.charging:
            from .config import CHARGE_TIME
            draw_bar(surface, 10, 35, 150, 4, min(1.0, pcomp.charge / CHARGE_TIME),
                     (255, 236, 130))

        # missiles (square counter with a missile icon, Super-Metroid style) --
        x = 236
        if loadout.max_missiles > 0:
            box = pygame.Rect(x, 10, 22, 22)
            pygame.draw.rect(surface, (52, 34, 24), box, border_radius=4)
            pygame.draw.rect(surface, (255, 170, 90), box, width=2, border_radius=4)
            surface.blit(self._missile_icon, (x + 3, 13))
            draw_text(surface, fonts, f"x{loadout.missiles:02d}", (x + 28, 12),
                      size=16, color=(255, 210, 150))
            x += 98

        # Nara cores -------------------------------------------------------
        for i in range(CORE_GOAL):
            cx = x + i * 20
            filled = i < loadout.cores
            col = (255, 120, 90) if filled else (70, 66, 80)
            pygame.draw.polygon(surface, col,
                                [(cx + 7, 12), (cx + 14, 19), (cx + 7, 26), (cx, 19)])

        self._draw_hud_map(surface, world, width)

    def _draw_hud_map(self, surface, world, width: int) -> None:
        """Small area map in the top-right corner (Super-Metroid style)."""
        tm = world.services.get("tilemap")
        if tm is None:
            return
        level = world.services.get("level")
        visited = world.services.get("visited") or set()
        scale = 2
        cols, rows = 44, 15
        pw, ph = cols * scale, rows * scale
        ox = width - pw - 10
        oy = (42 - ph) // 2 + 2

        back = pygame.Surface((pw + 6, ph + 6), pygame.SRCALPHA)
        back.fill((6, 10, 18, 215))
        surface.blit(back, (ox - 3, oy - 3))
        pygame.draw.rect(surface, (70, 110, 150), (ox - 3, oy - 3, pw + 6, ph + 6), 1)

        player = world.first(tag="player")
        if player is None:
            return
        ptr = player.get(Transform)
        cx = int((ptr.x + ptr.w / 2) // tm.tile_size)
        cy = int((ptr.y + ptr.h / 2) // tm.tile_size)
        x0 = max(0, min(cx - cols // 2, tm.width - cols))
        y0 = max(0, min(cy - rows // 2, tm.height - rows))

        zone_tiles = []
        if level is not None:
            ts = tm.tile_size
            for z in level.zones:
                if z.name in visited:
                    zr = z.rect
                    zone_tiles.append(pygame.Rect(zr.x // ts, zr.y // ts,
                                                  zr.w // ts, zr.h // ts))

        def revealed(tx, ty):
            return any(zr.collidepoint(tx, ty) for zr in zone_tiles)

        for row in range(rows):
            ty = y0 + row
            for col in range(cols):
                tx = x0 + col
                if not tm.in_bounds(tx, ty) or not revealed(tx, ty):
                    continue
                definition = tm.get_def(tx, ty)
                if definition.breakable:
                    c = (205, 155, 85)
                elif definition.hazard:
                    c = (235, 90, 60)
                elif definition.oneway:
                    c = (124, 112, 92)
                elif definition.solid:
                    c = (78, 104, 150)
                else:
                    continue
                pygame.draw.rect(surface, c, (ox + col * scale, oy + row * scale,
                                              scale, scale))
        pygame.draw.rect(surface, (120, 250, 255),
                         (ox + (cx - x0) * scale - 1, oy + (cy - y0) * scale - 1,
                          scale + 2, scale + 2))

    def _draw_boss(self, surface, world, fonts) -> None:
        boss_ent = world.first(Boss, tag="boss")
        if boss_ent is None:
            return
        boss: Boss = boss_ent.get(Boss)
        if not boss.active:
            return
        health: Health = boss_ent.get(Health)
        ratio = max(0.0, health.hp / health.max_hp)
        w = 300
        x = (surface.get_width() - w) // 2
        y = surface.get_height() - 34
        tag = boss_ent.get(Nametag)
        key = f"boss.{tag.name}" if tag is not None and tag.name else "hud.boss"
        name = t(key)
        if name == key:
            name = t("hud.boss")
        draw_text(surface, fonts, name, (x, y - 20), size=17, color=(255, 210, 210))
        draw_bar(surface, x, y, w, 14, ratio, (235, 90, 110), segments=10)

    def _draw_countdown(self, surface, fonts, value: float) -> None:
        w = surface.get_width()
        secs = max(0, int(math.ceil(value)))
        blink = int(value * 2) % 2 == 0
        color = (255, 90, 90) if blink else (255, 200, 120)
        draw_text(surface, fonts, t("hud.self_destruct"), (w // 2, 50), size=16,
                  color=(255, 150, 150), center=True, bold=True)
        draw_text(surface, fonts, f"{secs:02d}", (w // 2, 68), size=30,
                  color=color, center=True, bold=True)

    def _draw_toasts(self, surface, fonts, y: int = 52) -> None:
        for toast in self.toasts:
            alpha = min(1.0, toast.timer / 0.6)
            color = (255, 240, 180) if toast.kind == "ability" else (200, 230, 255)
            draw_text(surface, fonts, toast.title, (surface.get_width() // 2, y),
                      size=22, color=color, center=True, bold=True)
            if toast.subtitle:
                draw_text(surface, fonts, toast.subtitle,
                          (surface.get_width() // 2, y + 20), size=16,
                          color=(170, 190, 215), center=True)
            y += 46


# ---------------------------------------------------------------------------
# minimap
# ---------------------------------------------------------------------------

def draw_map(surface: pygame.Surface, world, fonts: Fonts, visited=None) -> None:
    """Exploration map: only areas the player has visited are revealed."""
    tm = world.services.get("tilemap")
    level = world.services.get("level")
    if tm is None:
        return
    scale = 2
    map_w = tm.width * scale
    map_h = tm.height * scale
    origin_x = (surface.get_width() - map_w) // 2
    origin_y = (surface.get_height() - map_h) // 2 + 6

    visited = visited or set()
    zone_rects = []
    if level is not None:
        for zone in level.zones:
            if zone.name in visited:
                r = zone.rect
                zone_rects.append(pygame.Rect(r.x // tm.tile_size, r.y // tm.tile_size,
                                              r.w // tm.tile_size, r.h // tm.tile_size))

    def revealed(tx, ty):
        for zr in zone_rects:
            if zr.collidepoint(tx, ty):
                return True
        return False

    panel = pygame.Surface((map_w + 8, map_h + 8), pygame.SRCALPHA)
    panel.fill((6, 8, 16, 230))
    surface.blit(panel, (origin_x - 4, origin_y - 4))

    for ty in range(tm.height):
        row = tm.grid[ty]
        for tx in range(tm.width):
            if not revealed(tx, ty):
                continue
            tile = row[tx]
            if tile == 0:
                continue
            definition = tm.tileset[tile]
            if definition.breakable:
                color = (200, 150, 80)
            elif definition.hazard:
                color = (230, 90, 60)
            elif definition.oneway:
                color = (120, 110, 90)
            else:
                color = (74, 92, 128)
            pygame.draw.rect(surface, color, (origin_x + tx * scale, origin_y + ty * scale,
                                              scale, scale))

    for ent in world.query():
        tr = ent.get(Transform)
        if tr is None:
            continue
        tx = tr.x + tr.w / 2
        ty = tr.y + tr.h / 2
        if not revealed(int(tx // tm.tile_size), int(ty // tm.tile_size)):
            continue
        cx = origin_x + int(tx / tm.tile_size * scale)
        cy = origin_y + int(ty / tm.tile_size * scale)
        if ent.has_tag("player"):
            pygame.draw.circle(surface, (120, 250, 255), (cx, cy), 3)
        elif ent.has_tag("save"):
            pygame.draw.rect(surface, (120, 240, 180), (cx - 2, cy - 2, 4, 4))
        elif ent.has_tag("boss"):
            pygame.draw.circle(surface, (255, 90, 110), (cx, cy), 3)
        elif ent.has_tag("gate"):
            pygame.draw.rect(surface, (150, 240, 255), (cx - 2, cy - 2, 4, 4))
        elif ent.has_tag("door"):
            pygame.draw.rect(surface, (255, 200, 120), (cx - 1, cy - 2, 3, 4))

    draw_text(surface, fonts, t("map.title"), (surface.get_width() // 2, origin_y - 24),
              size=20, color=(180, 220, 255), center=True)
    explored = len(zone_rects)
    total = len(level.zones) if level is not None else 0
    draw_text(surface, fonts, t("hud.explored", a=explored, b=total),
              (surface.get_width() // 2, origin_y + map_h + 12), size=15,
              color=(130, 155, 185), center=True)


# Backwards-compatible alias.
draw_minimap = draw_map


# ---------------------------------------------------------------------------
# Map tile glyphs (used by the room map and the export tool)
# ---------------------------------------------------------------------------

def _tile_char(definition) -> str:
    if definition.breakable:
        return "%"
    if definition.hazard:
        return "^" if definition.name == "spike" else "~"
    if definition.oneway:
        return "="
    if definition.solid:
        return "#"
    if definition.name in ("vine", "grate", "moss"):
        return ","
    return " "


def draw_room_map(surface: pygame.Surface, world, fonts: Fonts) -> None:
    """Room graph map (Super-Metroid style): boxes + door links."""
    graph = world.services.get("room_graph") or {}
    visited = world.services.get("visited_rooms") or set()
    current_id = world.services.get("current_room_id")
    draw_text(surface, fonts, t("map.title"), (surface.get_width() // 2, 8),
              size=22, color=(180, 220, 255), center=True, bold=True)
    if not graph:
        return

    xs = [g["x"] for g in graph.values()] + [g["x"] + g["w"] for g in graph.values()]
    ys = [g["y"] for g in graph.values()] + [g["y"] + g["h"] for g in graph.values()]
    minx, maxx, miny, maxy = min(xs), max(xs), min(ys), max(ys)
    bw, bh = max(1, maxx - minx), max(1, maxy - miny)

    panel = pygame.Rect(24, 40, surface.get_width() - 48, surface.get_height() - 108)
    scale = min(panel.w / bw, panel.h / bh, 12.0)
    ox = panel.centerx - bw * scale / 2 - minx * scale
    oy = panel.centery - bh * scale / 2 - miny * scale

    def scr(gx, gy):
        return ox + gx * scale, oy + gy * scale

    # door connectors first (behind the boxes)
    for rid, g in graph.items():
        if rid not in visited:
            continue
        for side, (to, dy) in g["doors"].items():
            if to not in visited or side not in ("left", "right"):
                continue
            ex = g["x"] if side == "left" else g["x"] + g["w"]
            x, y = scr(ex, g["y"] + dy + 1)
            pygame.draw.rect(surface, (255, 205, 130), (x - 2, y - 2, 4, 4))

    # room boxes
    for rid, g in graph.items():
        if rid not in visited:
            continue
        x, y = scr(g["x"], g["y"])
        rect = pygame.Rect(round(x), round(y), round(g["w"] * scale), round(g["h"] * scale))
        current = rid == current_id
        pygame.draw.rect(surface, (40, 74, 112) if current else (24, 32, 50), rect)
        pygame.draw.rect(surface, (120, 245, 255) if current else (84, 104, 146),
                         rect, 2 if current else 1)

    # the player inside the current room
    player = world.first(tag="player")
    tm = world.services.get("tilemap")
    if player is not None and tm is not None and current_id in graph \
            and current_id in visited:
        ptr = player.get(Transform)
        px = (ptr.x + ptr.w / 2) / tm.tile_size
        py = (ptr.y + ptr.h / 2) / tm.tile_size
        g = graph[current_id]
        cx, cy = scr(g["x"] + px, g["y"] + py)
        pygame.draw.circle(surface, (120, 250, 255), (int(cx), int(cy)), 3)
        pygame.draw.circle(surface, (10, 20, 30), (int(cx), int(cy)), 3, 1)

    total = len(graph)
    draw_text(surface, fonts, t("hud.explored", a=len(visited), b=total),
              (surface.get_width() // 2, surface.get_height() - 22), size=15,
              color=(130, 155, 185), center=True)
