"""Shared imports and helpers for the gameplay systems package."""

from __future__ import annotations

import math
import random
from typing import Optional

import pygame

from vesper.engine.ecs import System, World
from vesper.engine.physics import Body, Transform
from vesper.engine.render import Animator, Sprite

from .. import art
from ..components import (AI, Boss, ContactDamage, Door, Drops, Floating, Forms, Gate,
                         Health, Lifetime, Loadout, Pickup, Player, Projectile,
                         SaveStation, Ship, Spawner)
from ..config import (AIR_ACCEL, CHARGE_TIME, COYOTE_TIME, DASH_COOLDOWN,
                     DASH_SPEED, DASH_TIME, DAMAGE_INVULN, GRAVITY,
                     GROUND_ACCEL, GROUND_FRICTION, JUMP_BUFFER, JUMP_CUT,
                     JUMP_SPEED, MAX_FALL, MORPH_SPEED, RUN_SPEED, WEAPON_TIER,
                     WALL_JUMP_X, WALL_JUMP_Y, WALL_SLIDE_SPEED)
from ..items import apply_item
from ..i18n import t
from ..prefabs import spawn_enemy, spawn_pickup, spawn_projectile

def _particles(world: World):
    return world.services.get("particles")

def _registry(world: World):
    return world.services["registry"]

def _sfx(world: World, name: str, volume: float = 1.0) -> None:
    audio = _audio(world)
    if audio:
        audio.play(name, volume)

def _blocked(world: World, rect: pygame.Rect) -> bool:
    service = world.services.get("collision")
    if service is None:
        return False
    for solid, oneway in service.solids(world, rect):
        if oneway:
            continue
        if rect.colliderect(solid):
            return True
    return False

def _anim_aim(aim: str) -> str:
    if aim in ("up", "updiag"):
        return "up"
    if aim in ("down", "downdiag"):
        return "down"
    return "side"

def _approach(value: float, target: float, delta: float) -> float:
    if value < target:
        return min(value + delta, target)
    if value > target:
        return max(value - delta, target)
    return value

def _aim_vector(aim: str, facing: int) -> tuple:
    if aim == "up":
        return (0.0, -1.0)
    if aim == "down":
        return (0.0, 1.0)
    if aim == "updiag":
        return (facing * 0.7071, -0.7071)
    if aim == "downdiag":
        return (facing * 0.7071, 0.7071)
    return (float(facing), 0.0)

def apply_damage(world: World, ent, amount: float, source: Optional[tuple] = None,
                 knockback: float = 0.0, ignore_invuln: bool = False) -> bool:
    health: Health = ent.get(Health)
    if health is None or health.dead:
        return False
    if health.invuln > 0 and not ignore_invuln:
        return False
    health.hp -= amount
    if not ignore_invuln:
        health.invuln = DAMAGE_INVULN
    health.flash = 0.14
    if ent.has_tag("player"):
        player: Player = ent.get(Player)
        if player:
            player.hurt_timer = 0.30
        body: Body = ent.get(Body)
        if body is not None and source is not None and knockback:
            direction = -1 if source[0] > ent.get(Transform).x else 1
            body.vx = direction * knockback
            body.vy = -knockback * 0.45
        _sfx(world, "player_hurt")
        particles = _particles(world)
        if particles:
            tr = ent.get(Transform)
            particles.burst(tr.x + tr.w / 2, tr.y + tr.h / 2, (255, 90, 110), 10, 160)
        # shake the world and the HUD as if her suit panel takes the hit
        camera = world.services.get("camera")
        if camera is not None:
            camera.shake(7.0, 0.30)
        hud = world.services.get("hud")
        if hud is not None:
            hud.shake(9.0, 0.32)
    if health.hp <= 0:
        health.hp = 0
        health.dead = True
    if world.events:
        world.events.emit("damaged", entity=ent, amount=amount)
    return True

def _audio(world: World):
    return world.services.get("audio")
