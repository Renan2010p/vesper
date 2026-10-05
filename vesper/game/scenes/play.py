"""The gameplay scene: loads one independent room at a time."""

from __future__ import annotations

from typing import Optional

import pygame

from vesper.engine.ecs import World
from vesper.engine.physics import Body, CollisionService, PhysicsSystem, Transform
from vesper.engine.platform import EventType, Key
from vesper.engine.render import AnimatorSystem, SpriteDrawSystem
from vesper.engine.scene import Scene
from vesper.engine.save import SaveData

from .. import art
from ..components import Door, Gate, Health, Loadout
from ..config import GRAVITY, TILE, ZONE_COLORS
from ..hud import HUD
from ..i18n import t
from ..level import Zone, build_tileset
from ..prefabs import spawn_decoration, spawn_door, spawn_enemy, spawn_pickup, spawn_player, spawn_save_station, spawn_ship
from ..roomworld import build_room, build_room_graph
from ..rooms import START_ROOM
from ..systems import (AISystem, CameraSystem, DeathSystem, DoorSystem,
                       FloatingSystem, GateSystem, HazardSystem, PickupSystem,
                       PlayerControlSystem, ProjectileSystem, SaveStationSystem,
                       ShipSystem, SpawnerSystem, StatusSystem, TileMapDrawSystem,
                       TileMapForegroundSystem)


def _tile_solids(world: World, rect):
    tm = world.services["tilemap"]
    ts = tm.tile_size
    out = []
    for tx, ty in tm.tiles_overlapping(rect.x, rect.y, rect.w, rect.h):
        r = pygame.Rect(tx * ts, ty * ts, ts, ts)
        if not tm.in_bounds(tx, ty):
            out.append((r, False))
            continue
        definition = tm.get_def(tx, ty)
        if definition.solid:
            out.append((r, definition.oneway))
    return out


def _dynamic_solids(world: World, rect):
    out = []
    for ent in world.query(Gate):
        gate: Gate = ent.get(Gate)
        if not gate.open:
            out.append((ent.get(Transform).as_rect(), False))
    for ent in world.query(Door):
        door: Door = ent.get(Door)
        if door.anim < 0.5:
            out.append((ent.get(Transform).as_rect(), False))
    return out


class PlayScene(Scene):
    ROOM_FADE = 0.18

    def __init__(self, app, save: Optional[SaveData] = None, slot: int = 0) -> None:
        super().__init__(app)
        self.save_data = save
        self.slot = slot
        self.play_time = 0.0
        self.hud = HUD()
        self._dead = False
        self._victory_timer = 0.0
        self.bg_cache = {}
        self._was_ground = True
        self._room_trans = None
        self.current_zone = None
        self.current_room = None
        self.visited_rooms = set()
        self.room_graph = build_room_graph()
        self.tileset = build_tileset()
        self._build()
        self._load_room(save.spawn_zone if save and save.spawn_zone else START_ROOM,
                        spawn_pos=(save.spawn_x, save.spawn_y) if save else None,
                        announce=False)

    # ------------------------------------------------------------------
    # setup
    # ------------------------------------------------------------------
    def _build(self) -> None:
        app = self.app
        self.world.services.update({
            "registry": app.registry,
            "input": app.input,
            "audio": app.audio,
            "camera": app.camera,
            "particles": app.particles,
        })
        service = CollisionService()
        service.add_solids(_tile_solids)
        service.add_solids(_dynamic_solids)
        self.world.services["collision"] = service

        self.world.add_systems(
            AnimatorSystem(),
            FloatingSystem(),
            GateSystem(),
            DoorSystem(),
            SpawnerSystem(),
            AISystem(),
            PlayerControlSystem(),
            ProjectileSystem(),
            CameraSystem(),
            PhysicsSystem(gravity=GRAVITY),
            StatusSystem(),
            HazardSystem(),
            PickupSystem(),
            SaveStationSystem(),
            ShipSystem(),
            DeathSystem(),
            app.particles,
            TileMapDrawSystem(),
            SpriteDrawSystem(),
            TileMapForegroundSystem(),
        )
        self.world.start()
        app.particles.particles.clear()

        # the heroine persists across rooms
        self.player = spawn_player(self.world, 0, 0, self.save_data)
        self.world.services["player"] = self.player
        self.world.services["save_callback"] = self._save_game

        # background stars
        import random
        rng = random.Random(7)
        self.stars = [(rng.uniform(0, 512), rng.uniform(0, 288),
                       rng.choice((1, 1, 2)), rng.choice(
                           ((60, 80, 110), (90, 110, 150), (140, 160, 190))))
                      for _ in range(90)]

        events = self.world.events
        events.on("toast", lambda **k: self.hud.add_toast(
            k.get("title", ""), k.get("subtitle", ""), k.get("kind", "item")))
        events.on("player_died", lambda **k: setattr(self, "_dead", True))
        events.on("boss_defeated", lambda **k: setattr(self, "_victory_timer", 3.4))
        events.on("boss_engaged", lambda **k: self.hud.add_toast(
            t("toast.boss"), t("toast.boss_sub"), "ability"))

    # ------------------------------------------------------------------
    # rooms
    # ------------------------------------------------------------------
    def _load_room(self, room_id: str, enter: Optional[str] = None,
                   spawn_pos=None, announce: bool = True) -> None:
        room = build_room(room_id, self.tileset)
        tm = room.tilemap
        self.world.services["tilemap"] = tm

        zone = Zone(room.zone, pygame.Rect(0, 0, tm.pixel_width, tm.pixel_height),
                    ZONE_COLORS.get(room.zone, ZONE_COLORS["unknown"]))
        level = _RoomLevel(zone, room)
        self.world.services["level"] = level
        self.world.services["visited"] = {room.zone}
        self.visited_rooms.add(room_id)
        self.world.services["visited_rooms"] = self.visited_rooms
        self.world.services["room_graph"] = self.room_graph
        self.world.services["current_room_id"] = room_id
        self.current_zone = zone
        self.current_room = room

        # clear the previous room's entities (keep the player)
        for ent in list(self.world.entities.values()):
            if "room" in ent.tags or ent.has_tag("projectile"):
                ent.destroy()
        self.world.flush()
        self.app.particles.particles.clear()

        self._populate_room(room)

        # place the heroine at the matching entrance door (if any)
        player = self.player
        tr = player.get(Transform)
        body = player.get(Body)
        placed = False
        if enter in ("left", "right"):
            for ent in self.world.query(Transform, Door):
                dtr = ent.get(Transform)
                on_side = (dtr.x < 2 * TILE) if enter == "left" else \
                    (dtr.x > (tm.width - 2) * TILE)
                if not on_side:
                    continue
                if enter == "left":
                    tr.x = dtr.x + dtr.w + 2
                else:
                    tr.x = dtr.x - tr.w - 2
                tr.y = dtr.y + dtr.h - tr.h
                placed = True
                break
        if spawn_pos is not None:
            tr.x, tr.y = spawn_pos
        elif not placed:
            tr.x, tr.y = room.spawn
        body.vx = body.vy = 0.0
        body.gravity = True
        health: Health = player.get(Health)
        health.dead = False
        health.invuln = max(health.invuln, 0.6)

        self.app.camera.set_bounds_rect(pygame.Rect(0, 0, tm.pixel_width, tm.pixel_height))
        self.app.camera.snap(tr.x + tr.w / 2, tr.y + tr.h / 2)
        self._was_ground = False

        if announce:
            self.hud.add_toast(t(room.label), "", "save")
        self._room_trans = None

    def _populate_room(self, room) -> None:
        w = self.world
        for spec in room.doors:
            ent = spawn_door(w, spec["x"], spec["y"], spec["w"], spec["h"],
                             tier=spec.get("tier", 0), axis=spec.get("axis", "v"))
            door: Door = ent.get(Door)
            door.target = spec.get("target", "")
            door.enter = spec.get("enter", "")
            ent.tag("room")
        if room.ship:
            spawn_ship(w, room.ship[0], room.ship[1]).tag("room")
        for x, y in room.saves:
            spawn_save_station(w, x, y).tag("room")
        for item, x, y in room.pickups:
            spawn_pickup(w, item, x, y).tag("room")
        for name, x, y in room.enemies:
            spawn_enemy(w, name, x, y).tag("room")
        for kind, dx, ground_y in room.decorations:
            factory = art.SURFACE_DECOR.get(kind)
            if factory is None:
                continue
            surf = factory()
            layer = 1 if kind == "puddle" else 2
            spawn_decoration(w, surf, dx - surf.get_width() / 2,
                             ground_y - surf.get_height(), layer=layer).tag("room")

    def _update_room_transition(self, dt: float) -> None:
        trans = self._room_trans
        if trans is None:
            player = self.world.first(tag="player")
            if player is None:
                return
            prect = player.get(Transform).as_rect().inflate(2, 2)
            for ent in self.world.query(Transform, Door):
                door: Door = ent.get(Door)
                if door.open and door.target and prect.colliderect(
                        ent.get(Transform).as_rect()):
                    self._room_trans = {"t": 0.0, "done": False, "target": door.target,
                                        "enter": door.enter}
                    break
        else:
            trans["t"] += dt
            if trans["t"] >= self.ROOM_FADE and not trans["done"]:
                trans["done"] = True
                self._load_room(trans["target"], enter=trans["enter"])
            if trans["t"] >= self.ROOM_FADE * 2:
                self._room_trans = None

    def _draw_room_fade(self, surface: pygame.Surface) -> None:
        if self._room_trans is None:
            return
        tt = self._room_trans["t"]
        half = self.ROOM_FADE
        alpha = 255 * (tt / half) if tt < half else 255 * (1 - (tt - half) / half)
        alpha = max(0, min(255, int(alpha)))
        overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, alpha))
        surface.blit(overlay, (0, 0))

    # ------------------------------------------------------------------
    # lifecycle
    # ------------------------------------------------------------------
    def on_enter(self) -> None:
        self.app.audio.start_music()

    def handle_event(self, event) -> None:
        if event.type == EventType.KEYDOWN:
            pause_keys = self.app.input.bindings.get("pause", ())
            up_keys = self.app.input.bindings.get("up", ())
            if self.world.services.get("ship_nearby") and event.key in up_keys:
                self.app.scenes.switch("ship", play=self)
            elif event.key in pause_keys:
                self.app.scenes.switch("pause", play=self)
            elif event.key == Key.M:
                self.app.audio.set_enabled(not self.app.audio.enabled)

    def update(self, dt: float) -> None:
        self.play_time += dt
        self.world.update(dt)
        self.hud.update(dt)

        player = self.world.first(tag="player")
        if player is not None:
            body = player.get(Body)
            self._was_ground = body.on_ground

        self._update_room_transition(dt)

        if self._dead:
            self._dead = False
            self._respawn()

        if self._victory_timer > 0:
            self._victory_timer -= dt
            if self._victory_timer <= 0:
                self.app.switch_scene("end", win=True,
                                      stats={"time": self.play_time,
                                             "kills": self._kills()})

    def draw(self, surface: pygame.Surface) -> None:
        self._draw_background(surface)
        self.world.draw(surface, self.app.camera)
        if self.current_zone is not None and self.current_zone.name == "surface":
            self._draw_rain(surface)
        if self.world.services.get("ship_nearby"):
            self._draw_ship_prompt(surface)
        self.hud.draw(surface, self.world, self.app.fonts)
        self._draw_room_fade(surface)

    def _draw_ship_prompt(self, surface: pygame.Surface) -> None:
        from vesper.engine.ui import draw_panel, draw_text
        w = surface.get_width()
        panel = pygame.Rect(w // 2 - 96, surface.get_height() - 52, 192, 30)
        draw_panel(surface, panel, fill=(8, 12, 20, 210), border=(90, 240, 255))
        draw_text(surface, self.app.fonts, t("ship.board"), (w // 2, panel.centery),
                  size=17, color=(150, 240, 255), center=True, bold=True)

    # ------------------------------------------------------------------
    # background & weather
    # ------------------------------------------------------------------
    def _draw_background(self, surface: pygame.Surface) -> None:
        from vesper.engine.sprites import vertical_gradient
        zone = self.current_zone or self.level_zones()[0]
        surf = self.bg_cache.get(zone.name)
        if surf is None:
            surf = vertical_gradient(surface.get_width(), surface.get_height(),
                                     zone.colors[0], zone.colors[1])
            self.bg_cache[zone.name] = surf
        surface.blit(surf, (0, 0))
        cam = self.app.camera
        w, h = surface.get_size()
        for sx, sy, r, color in self.stars:
            x = (sx - cam.x * 0.25) % (w + 60) - 30
            y = (sy - cam.y * 0.18) % (h + 60) - 30
            pygame.draw.circle(surface, color, (int(x), int(y)), r)
        if zone.name == "surface":
            # simple stormy sky: just the black hole the planet orbits
            bh_x = int(w * 0.74 - cam.x * 0.05) % (w + 320) - 160
            art.draw_black_hole(surface, bh_x, int(h * 0.22), 44, self.play_time)

    def level_zones(self):
        lvl = self.world.services.get("level")
        return lvl.zones if lvl is not None else []

    def _draw_rain(self, surface):
        """Simple single-layer rain for the surface."""
        w, h = surface.get_size()
        t = self.play_time
        for i in range(60):
            x = (i * 61 + int(t * 500)) % (w + 40) - 20
            y = (i * 97 + int(t * 900)) % (h + 40) - 20
            pygame.draw.line(surface, (120, 150, 190), (x, y), (x - 4, y + 16), 1)

    # ------------------------------------------------------------------
    # helpers
    # ------------------------------------------------------------------
    def _kills(self) -> int:
        return self.world.services.get("kill_count", 0)

    def _respawn(self) -> None:
        room = self.current_room
        if room is not None:
            self._load_room(room.id, spawn_pos=room.spawn, announce=False)
        self.hud.add_toast(t("toast.recovered"), t("toast.recovered_sub"), "save")

    def _save_game(self, player) -> None:
        tr = player.get(Transform)
        health: Health = player.get(Health)
        loadout: Loadout = player.get(Loadout)
        current = self.current_room.id if self.current_room else START_ROOM
        data = SaveData(
            play_time=self.play_time,
            spawn_zone=current, spawn_x=tr.x, spawn_y=tr.y,
            health=int(health.hp), max_health=health.max_hp,
            missiles=loadout.missiles, max_missiles=loadout.max_missiles,
            abilities=sorted(loadout.abilities), items=sorted(loadout.items),
            flags={"cores": loadout.cores,
                   "energy_tanks": loadout.energy_tanks,
                   "missile_tanks": loadout.missile_tanks},
        )
        self.app.save.save(data, self.slot)


class _RoomLevel:
    """Minimal LevelData-like object for the HUD / background."""

    def __init__(self, zone, room) -> None:
        self.zones = [zone]
        self.rooms = [{"name": room.id, "label": room.label, "x": 0, "y": 0,
                       "w": room.tilemap.width, "h": room.tilemap.height}]

    def zone_at(self, px, py):
        return self.zones[0]
