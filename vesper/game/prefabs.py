"""Entity prefabs.

A prefab is a pure function ``spawn_*(world, ...) -> entity`` that assembles
components.  Enemies are data-driven: an :class:`EnemyDef` is registered under
``enemy/<name>`` and :func:`spawn_enemy` turns it into an entity.  This is the
single place where "what an enemy is made of" is decided.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional

import pygame

from vesper.engine.ecs import World
from vesper.engine.physics import Body, Transform
from vesper.engine.render import Animation, Animator, Sprite

from . import art
from .components import (AI, Boss, ContactDamage, Door, Drops, Floating, Forms, Gate,
                         Health, Lifetime, Loadout, Nametag, Pickup, Player,
                         Projectile, SaveStation, Ship, Spawner)
from .config import BASE_HEALTH, BASE_MISSILES, PLAYER_H, PLAYER_W


@dataclass
class EnemyDef:
    name: str
    art: Callable[[], Dict[str, Animation]]
    behavior: str = "patrol"
    hp: int = 20
    contact_damage: int = 8
    w: float = 16.0
    h: float = 16.0
    flying: bool = False
    speed: float = 70.0
    gravity_scale: float = 1.0
    sprite_layer: int = 0
    tags: tuple = ()
    drops: List[str] = field(default_factory=list)
    drop_chance: float = 0.15
    boss: bool = False
    params: dict = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Player
# ---------------------------------------------------------------------------

def spawn_player(world: World, x: float, y: float, save=None) -> object:
    anims = art.player_animations()
    morph = art.morph_animations()
    first = anims["idle_side"].frames[0]
    ent = world.create(
        Transform(x, y, PLAYER_W, PLAYER_H),
        Body(),
        Sprite(first, offset=(-2, -2), layer=10),
        Animator(anims, "idle_side"),
        Forms(human_anims=anims, morph_anims=morph,
              human_size=(PLAYER_W, PLAYER_H), morph_size=(14.0, 14.0)),
        Player(respawn=(x, y)),
        Health(BASE_HEALTH, BASE_HEALTH, team="player"),
        Loadout(missiles=BASE_MISSILES),
        tags=("player",),
    )
    if save is not None:
        _restore(world, ent, save)
    return ent


def _restore(world: World, ent, save) -> None:
    health = ent.get(Health)
    loadout = ent.get(Loadout)
    health.max_hp = save.max_health
    health.hp = save.health
    loadout.missiles = save.missiles
    loadout.max_missiles = save.max_missiles
    loadout.abilities = set(save.abilities)
    loadout.items = set(save.items)
    loadout.energy_tanks = save.flags.get("energy_tanks", 0)
    loadout.missile_tanks = save.flags.get("missile_tanks", 0)
    loadout.cores = save.flags.get("cores", 0)


# ---------------------------------------------------------------------------
# Projectiles
# ---------------------------------------------------------------------------

def spawn_projectile(world: World, kind: str, x: float, y: float, vx: float, vy: float,
                     damage: int, team: str = "player", owner: int = 0,
                     breaks_tiles: bool = False, break_radius: int = 0, pierce: int = 0,
                     gravity: float = 0.0, homing: float = 0.0,
                     knockback: float = 0.0, tier: int = 0) -> object:
    surface = art.projectile_surface(kind)
    if kind == "super_missile":
        surface = pygame.transform.scale(surface, (surface.get_width() + 6, surface.get_height() + 4))
    w, h = surface.get_size()
    ent = world.create(
        Transform(x - w / 2, y - h / 2, w, h),
        Body(gravity=False, enabled=True),
        Sprite(surface, layer=6),
        Projectile(damage=damage, team=team, owner=owner, breaks_tiles=breaks_tiles,
                   break_radius=break_radius, pierce=pierce, gravity=gravity,
                   homing=homing, knockback=knockback, tier=tier),
        Lifetime(remaining=2.4),
        tags=("projectile", team),
    )
    body = ent.get(Body)
    body.vx, body.vy = vx, vy
    return ent


# ---------------------------------------------------------------------------
# Enemies
# ---------------------------------------------------------------------------

def spawn_enemy(world: World, name: str, x: float, y: float, **overrides) -> object:
    registry = world.services["registry"]
    defn: EnemyDef = registry.get("enemy", name)
    anims = defn.art()
    key = "idle" if "idle" in anims else next(iter(anims))
    first = anims[key].frames[0]
    w = overrides.get("w", defn.w)
    h = overrides.get("h", defn.h)
    hp = overrides.get("hp", defn.hp)
    body = Body(gravity=not defn.flying, gravity_scale=defn.gravity_scale)
    comps = [
        Transform(x - w / 2, y - h / 2, w, h),
        body,
        Sprite(first, layer=defn.sprite_layer + 1),
        Animator(anims, key),
        Health(hp, hp, team="enemy"),
        ContactDamage(overrides.get("contact_damage", defn.contact_damage)),
        AI(defn.behavior, origin=(x, y), range=defn.params.get("range", 120.0),
           state=dict(defn.params)),
        Nametag(name),
        Drops(list(defn.drops), defn.drop_chance),
    ]
    tags = tuple(defn.tags) + (("boss",) if defn.boss else ("enemy",))
    if defn.flying:
        comps.append(Floating(amplitude=3.0, speed=2.2, base_y=y - h / 2))
    if defn.boss:
        comps.append(Boss(home_x=x, home_y=y, active=False))
    ent = world.create(*comps, tags=tags)
    # publish the definition for systems that need stats
    world.services.setdefault("enemy_defs", {})[ent.id] = defn
    return ent


# ---------------------------------------------------------------------------
# Pickups / props
# ---------------------------------------------------------------------------

def spawn_pickup(world: World, item_id: str, x: float, y: float, amount: int = 1) -> object:
    surface = art.item_surface(item_id)
    ent = world.create(
        Transform(x - 10, y - 10, 20, 20),
        Sprite(surface, layer=4),
        Pickup(item_id=item_id, amount=amount),
        Floating(amplitude=3.0, speed=2.6, phase=(x * 0.01) % 6.28, base_y=y - 10),
        tags=("pickup",),
    )
    return ent


def spawn_gate(world: World, x: float, y: float, w: float, h: float,
               required: Optional[str] = None, cores_needed: int = 0,
               label: str = "") -> object:
    closed = art.gate_surface(int(w), int(h))
    opened = art.gate_open_surface(int(w), int(h))
    ent = world.create(
        Transform(x, y, w, h),
        Sprite(closed, layer=2),
        Gate(required=required or "", cores_needed=cores_needed, label=label),
        Nametag("gate"),
        Drops(),
        tags=("gate", "solid"),
    )
    world.services.setdefault("gate_art", {})[ent.id] = opened
    return ent


def spawn_save_station(world: World, x: float, y: float) -> object:
    return world.create(
        Transform(x - 10, y - 26, 20, 26),
        Sprite(art.save_surface(), layer=3),
        SaveStation(),
        Nametag("save"),
        tags=("save",),
    )


def spawn_ship(world: World, x: float, y: float) -> object:
    """Big boardable gunship. ``x`` is the centre, ``y`` the ground line."""
    surface = art.gunship_surface()
    w, h = surface.get_size()
    return world.create(
        Transform(x - w / 2, y - h, w, h),
        Sprite(surface, layer=2),
        Ship(),
        Nametag("ship"),
        Drops(),
        tags=("ship", "interact"),
    )


def spawn_door(world: World, x: float, y: float, w: float, h: float,
               tier: int = 0, axis: str = "h") -> object:
    from .config import DOOR_COLORS, TIER_NAME
    color = DOOR_COLORS.get(TIER_NAME[min(tier, len(TIER_NAME) - 1)], (255, 255, 255))
    frames = art.door_frames(int(w), int(h), color)
    ent = world.create(
        Transform(x, y, w, h),
        Sprite(frames[0], layer=7),
        Door(tier=tier, axis=axis),
        Nametag("door"),
        Drops(),
        tags=("door", "solid"),
    )
    world.services.setdefault("door_frames", {})[ent.id] = frames
    return ent


def spawn_spawner(world: World, x: float, y: float, prefab: str, interval: float = 5.0,
                  cap: int = 3, radius: float = 140.0) -> object:
    return world.create(
        Transform(x, y, 4, 4),
        Spawner(prefab=prefab, interval=interval, cap=cap, radius=radius, timer=interval),
        Drops(),
        tags=("spawner",),
    )


def spawn_decoration(world: World, surface: pygame.Surface, x: float, y: float,
                     layer: int = 1) -> object:
    return world.create(Transform(x, y, *surface.get_size()), Sprite(surface, layer=layer),
                        Drops())


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

def register_prefabs(registry) -> None:
    registry.register("prefab", "player", spawn_player)
    registry.register("prefab", "projectile", spawn_projectile)
    registry.register("prefab", "enemy", spawn_enemy)
    registry.register("prefab", "pickup", spawn_pickup)
    registry.register("prefab", "gate", spawn_gate)
    registry.register("prefab", "save", spawn_save_station)
    registry.register("prefab", "door", spawn_door)
    registry.register("prefab", "ship", spawn_ship)
    registry.register("prefab", "spawner", spawn_spawner)
    registry.register("prefab", "decoration", spawn_decoration)
