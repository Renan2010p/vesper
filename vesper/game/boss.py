"""The final boss: the Warden of the Aegis Core.

A boss is just an enemy with the ``boss`` tag, an :class:`EnemyDef` and a
dedicated behaviour.  Nothing in the engine knows bosses exist, which keeps the
feature modular and lets mods add their own.
"""

from __future__ import annotations

import math
import random

from vesper.engine.ecs import World
from vesper.engine.physics import Body, Transform
from vesper.engine.render import Animator, Sprite

from . import art
from .components import AI, Boss, Health
from .prefabs import EnemyDef, spawn_enemy, spawn_projectile


def _player(world: World):
    return world.first(tag="player")


def _fire_ring(world, ent, count: int, speed: float, phase: float, damage: int) -> None:
    tr: Transform = ent.get(Transform)
    cx, cy = tr.x + tr.w / 2, tr.y + tr.h / 2
    for i in range(count):
        a = phase + i * math.tau / count
        spawn_projectile(world, "boss_orb", cx + math.cos(a) * 24, cy + math.sin(a) * 24,
                         math.cos(a) * speed, math.sin(a) * speed, damage,
                         team="enemy", owner=ent.id)


def _fire_spread(world, ent, count: int, speed: float, damage: int) -> None:
    player = _player(world)
    tr: Transform = ent.get(Transform)
    cx, cy = tr.x + tr.w / 2, tr.y + tr.h / 2
    if player is None:
        base = 0.0
    else:
        p_tr: Transform = player.get(Transform)
        base = math.atan2((p_tr.y + p_tr.h / 2) - cy, (p_tr.x + p_tr.w / 2) - cx)
    for i in range(count):
        offset = (i - (count - 1) / 2) * 0.22
        a = base + offset
        spawn_projectile(world, "boss_orb", cx + math.cos(a) * 24, cy + math.sin(a) * 24,
                         math.cos(a) * speed, math.sin(a) * speed, damage,
                         team="enemy", owner=ent.id)


def ai_warden(world: World, ent, dt: float) -> None:
    boss: Boss = ent.get(Boss)
    health: Health = ent.get(Health)
    tr: Transform = ent.get(Transform)
    sprite: Sprite = ent.get(Sprite)
    animator: Animator = ent.get(Animator)
    ai: AI = ent.get(AI)

    player = _player(world)
    if player is None:
        return

    if not boss.active:
        p_tr: Transform = player.get(Transform)
        if math.hypot(p_tr.x - tr.x, p_tr.y - tr.y) < 300:
            boss.active = True
            boss.intro = 1.4
            if world.events:
                world.events.emit("boss_engaged", entity=ent)
        return

    if boss.intro > 0:
        boss.intro -= dt
        tr.y = boss.home_y + math.sin(boss.intro * 8) * 6
        return

    boss.timer += dt
    # change phase at half health
    phase = 0 if health.hp > health.max_hp * 0.5 else 1
    if phase != boss.phase:
        boss.phase = phase
        boss.shot_cd = 0.4
        animator.play("angry")
        if world.events:
            world.events.emit("boss_phase", phase=phase)

    # hover motion
    tr.x = boss.home_x - tr.w / 2 + math.sin(boss.timer * 0.9) * 70
    tr.y = boss.home_y - tr.h / 2 + math.sin(boss.timer * 2.1) * 26

    boss.shot_cd -= dt
    if boss.shot_cd <= 0:
        boss.pattern = (boss.pattern + 1) % 4
        if boss.pattern == 0:
            _fire_spread(world, ent, 3, 230.0, 12)
            boss.shot_cd = 1.5 if phase == 0 else 1.0
        elif boss.pattern == 1:
            _fire_ring(world, ent, 10, 170.0, boss.timer, 10)
            boss.shot_cd = 1.8 if phase == 0 else 1.2
        elif boss.pattern == 2:
            _fire_spread(world, ent, 5, 210.0, 12)
            boss.shot_cd = 2.0 if phase == 0 else 1.3
        else:
            # spawn minions in the second phase
            if phase == 1:
                existing = sum(1 for e in world.query(Health, tag="enemy")
                               if not e.has_tag("boss"))
                if existing < 3:
                    for _ in range(2):
                        angle = random.uniform(0, math.tau)
                        spawn_enemy(world, "flyer",
                                    tr.x + tr.w / 2 + math.cos(angle) * 50,
                                    tr.y + tr.h / 2 + math.sin(angle) * 50)
            boss.shot_cd = 2.4

    sprite.flip_x = False


def register_boss(registry) -> None:
    warden = EnemyDef(
        "warden", art.boss_art, "warden", hp=520, contact_damage=22,
        w=48, h=48, flying=True, boss=True, sprite_layer=1,
        params={"range": 400.0},
    )
    registry.register("enemy", warden.name, warden)
    registry.register("ai", "warden", ai_warden)
