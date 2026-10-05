"""Enemy catalogue and AI behaviours.

Behaviours are registered under ``ai/<name>`` and referenced by
:class:`~vesper.game.prefabs.EnemyDef.behavior`.  Adding a creature means adding
an art function, an ``EnemyDef`` and (optionally) a new behaviour here.
"""

from __future__ import annotations

import math
import random
from typing import Dict

import pygame

from vesper.engine.ecs import World
from vesper.engine.physics import Body, Transform
from vesper.engine.render import Animator, Sprite

from . import art
from .components import AI, Floating, Health
from .prefabs import EnemyDef, spawn_projectile

# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _tilemap(world: World):
    return world.services.get("tilemap")


def _solid_at(world: World, px: float, py: float) -> bool:
    tm = _tilemap(world)
    if tm is None:
        return False
    ts = tm.tile_size
    return tm.is_solid(int(px // ts), int(py // ts))


def _ground_ahead(world: World, tr: Transform, direction: int) -> bool:
    x = tr.x + (tr.w + 2) if direction > 0 else tr.x - 2
    return _solid_at(world, x, tr.y + tr.h + 3)


def _player(world: World):
    return world.first(tag="player")


def _dist(a, b) -> float:
    return math.hypot(a[0] - b[0], a[1] - b[1])


def _face(sprite: Sprite, direction: int) -> None:
    sprite.flip_x = direction < 0


# ---------------------------------------------------------------------------
# behaviours
# ---------------------------------------------------------------------------

def ai_patrol(world: World, ent, dt: float) -> None:
    body: Body = ent.get(Body)
    tr: Transform = ent.get(Transform)
    ai: AI = ent.get(AI)
    sprite: Sprite = ent.get(Sprite)
    speed = ai.state.get("speed", 70.0)
    direction = ai.state.get("dir", 1)
    if body.on_wall_right:
        direction = -1
    elif body.on_wall_left:
        direction = 1
    elif body.on_ground and not _ground_ahead(world, tr, direction):
        direction *= -1
    ai.state["dir"] = direction
    body.vx = speed * direction
    _face(sprite, direction)


def ai_hover(world: World, ent, dt: float) -> None:
    """Slow horizontal drift around the spawn point."""
    body: Body = ent.get(Body)
    tr: Transform = ent.get(Transform)
    ai: AI = ent.get(AI)
    sprite: Sprite = ent.get(Sprite)
    speed = ai.state.get("speed", 55.0)
    direction = ai.state.get("dir", 1)
    ox = ai.origin[0]
    if tr.x + tr.w / 2 > ox + ai.range:
        direction = -1
    elif tr.x + tr.w / 2 < ox - ai.range:
        direction = 1
    if body.on_wall_left:
        direction = 1
    elif body.on_wall_right:
        direction = -1
    ai.state["dir"] = direction
    body.vx = speed * direction
    _face(sprite, direction)


def ai_chase(world: World, ent, dt: float) -> None:
    """Fly toward the player when close, else hover."""
    player = _player(world)
    tr: Transform = ent.get(Transform)
    body: Body = ent.get(Body)
    sprite: Sprite = ent.get(Sprite)
    ai: AI = ent.get(AI)
    speed = ai.state.get("speed", 90.0)
    if player is None:
        return ai_hover(world, ent, dt)
    p_tr: Transform = player.get(Transform)
    dx = (p_tr.x + p_tr.w / 2) - (tr.x + tr.w / 2)
    dy = (p_tr.y + p_tr.h / 2) - (tr.y + tr.h / 2)
    dist = math.hypot(dx, dy)
    if dist < ai.range and dist > 1:
        body.vx = speed * dx / dist
        body.vy = speed * dy / dist
    else:
        body.vx *= 0.9
    _face(sprite, 1 if dx >= 0 else -1)


def ai_turret(world: World, ent, dt: float) -> None:
    ai: AI = ent.get(AI)
    tr: Transform = ent.get(Transform)
    sprite: Sprite = ent.get(Sprite)
    ai.cooldown -= dt
    player = _player(world)
    if player is None:
        return
    p_tr: Transform = player.get(Transform)
    pc = (p_tr.x + p_tr.w / 2, p_tr.y + p_tr.h / 2)
    ec = (tr.x + tr.w / 2, tr.y + tr.h / 2)
    dist = _dist(pc, ec)
    _face(sprite, 1 if pc[0] >= ec[0] else -1)
    if dist < ai.range and ai.cooldown <= 0:
        ai.cooldown = ai.state.get("cooldown", 1.6)
        speed = ai.state.get("shot_speed", 220.0)
        angle = math.atan2(pc[1] - ec[1], pc[0] - ec[0])
        spawn_projectile(world, "enemy", ec[0] + math.cos(angle) * 10,
                         ec[1] + math.sin(angle) * 10,
                         math.cos(angle) * speed, math.sin(angle) * speed,
                         ai.state.get("damage", 10), team="enemy", owner=ent.id)


def ai_jumper(world: World, ent, dt: float) -> None:
    body: Body = ent.get(Body)
    tr: Transform = ent.get(Transform)
    sprite: Sprite = ent.get(Sprite)
    ai: AI = ent.get(AI)
    ai.cooldown -= dt
    player = _player(world)
    if body.on_ground:
        body.vx *= 0.8
        if ai.cooldown <= 0:
            ai.cooldown = ai.state.get("cooldown", 1.8)
            direction = 1
            if player is not None:
                p_tr: Transform = player.get(Transform)
                direction = 1 if p_tr.x > tr.x else -1
            body.vy = -ai.state.get("jump", 520.0)
            body.vx = direction * ai.state.get("speed", 150.0)
            _face(sprite, direction)
    else:
        sprite.flip_x = body.vx < 0


def ai_static(world: World, ent, dt: float) -> None:
    pass


def ai_ambush(world: World, ent, dt: float) -> None:
    """Sleep until the player is near, then chase."""
    player = _player(world)
    ai: AI = ent.get(AI)
    if player is None:
        return
    tr: Transform = ent.get(Transform)
    p_tr: Transform = player.get(Transform)
    awake = ai.state.get("awake", False)
    if not awake and _dist((tr.x, tr.y), (p_tr.x, p_tr.y)) < ai.range:
        ai.state["awake"] = True
    if ai.state.get("awake"):
        ai_chase(world, ent, dt)


# ---------------------------------------------------------------------------
# defs
# ---------------------------------------------------------------------------

def register_enemies(registry) -> None:
    defs = [
        EnemyDef("crawler", art.crawler_art, "patrol", hp=18, contact_damage=8,
                 w=16, h=14, speed=58.0, drops=["energy_tank"], drop_chance=0.05),
        EnemyDef("skitter", art.crawler_art, "patrol", hp=12, contact_damage=6,
                 w=16, h=14, speed=110.0, params={"speed": 110.0},
                 drops=["missile_tank"], drop_chance=0.05),
        EnemyDef("flyer", art.flyer_art, "hover", hp=14, contact_damage=10,
                 w=20, h=14, flying=True, speed=60.0, params={"speed": 60.0, "range": 70.0}),
        EnemyDef("hunter_drone", art.flyer_art, "chase", hp=20, contact_damage=12,
                 w=20, h=14, flying=True, params={"speed": 95.0, "range": 150.0}),
        EnemyDef("turret", art.turret_art, "turret", hp=30, contact_damage=6,
                 w=18, h=18, speed=0.0,
                 params={"range": 190.0, "cooldown": 1.5, "shot_speed": 230.0, "damage": 10},
                 drops=["energy_tank"], drop_chance=0.1),
        EnemyDef("jumper", art.jumper_art, "jumper", hp=26, contact_damage=10,
                 w=16, h=16, params={"cooldown": 1.7, "jump": 520.0, "speed": 150.0},
                 drops=["missile_tank"], drop_chance=0.08),
    ]
    for d in defs:
        registry.register("enemy", d.name, d)

    registry.register("ai", "patrol", ai_patrol)
    registry.register("ai", "hover", ai_hover)
    registry.register("ai", "chase", ai_chase)
    registry.register("ai", "turret", ai_turret)
    registry.register("ai", "jumper", ai_jumper)
    registry.register("ai", "static", ai_static)
    registry.register("ai", "ambush", ai_ambush)
