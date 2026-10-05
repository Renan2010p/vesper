"""Generic AABB physics against a pluggable collision service.

The engine defines the movement primitives (:class:`Transform`,
:class:`Body`) and the integrator.  *What* is solid is delegated to
``world.services["collision"]``, so the same physics drives tiles, moving
platforms and closed doors without modification.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Callable, List, Tuple

import pygame

from .ecs import System, World

Rect = pygame.Rect


@dataclass
class Transform:
    x: float = 0.0
    y: float = 0.0
    w: float = 16.0
    h: float = 16.0

    def as_rect(self) -> Rect:
        return Rect(round(self.x), round(self.y), round(self.w), round(self.h))

    @property
    def center(self) -> Tuple[float, float]:
        return self.x + self.w / 2, self.y + self.h / 2


@dataclass
class Body:
    vx: float = 0.0
    vy: float = 0.0
    gravity_scale: float = 1.0
    max_fall: float = 900.0
    friction: float = 1.0
    on_ground: bool = False
    on_ceiling: bool = False
    on_wall_left: bool = False
    on_wall_right: bool = False
    #: if False the body floats (flyers, projectiles)
    gravity: bool = True
    #: if False collision is skipped entirely (used by dying / cutscene bodies)
    enabled: bool = True
    #: mark true when the body should ignore one-way platforms (dropping down)
    drop_through: bool = False


class CollisionService:
    """Aggregates solid providers registered by the game layer.

    A provider is ``callable(world, rect) -> list`` returning
    ``[(pygame.Rect, oneway: bool), ...]``.
    """

    def __init__(self) -> None:
        self.solid_providers: List[Callable] = []

    def add_solids(self, provider: Callable) -> None:
        self.solid_providers.append(provider)

    def solids(self, world: World, rect: Rect) -> List[Tuple[Rect, bool]]:
        out: List[Tuple[Rect, bool]] = []
        for provider in self.solid_providers:
            out.extend(provider(world, rect))
        return out


def _collision_service(world: World) -> CollisionService:
    service = world.services.get("collision")
    if service is None:
        service = CollisionService()
        world.services["collision"] = service
    return service


def move_and_collide(world: World, transform: Transform, body: Body, dx: float,
                     dy: float, max_step: float = 6.0) -> None:
    """Move by ``(dx, dy)`` resolving against solids, updating ground flags.

    Movement is sub-stepped so fast bodies (dashes, projectiles) cannot tunnel
    through thin walls.
    """
    service = _collision_service(world)
    distance = max(abs(dx), abs(dy))
    steps = max(1, int(math.ceil(distance / max_step))) if max_step > 0 else 1
    rem_x, rem_y = dx, dy

    body.on_ground = False
    body.on_ceiling = False
    body.on_wall_left = False
    body.on_wall_right = False

    for _ in range(steps):
        # resolve vertically first so a fast landing is cleared before the
        # horizontal pass (otherwise the floor can push the body sideways)
        transform.y += rem_y / steps
        _resolve_y(world, service, transform, body)
        if body.vy == 0.0:
            rem_y = 0.0            # stop sinking once we've hit something
        transform.x += rem_x / steps
        _resolve_x(world, service, transform, body)
        if body.vx == 0.0:
            rem_x = 0.0


def _overlap(t: Transform, r: Rect) -> bool:
    return (t.x < r.right and t.x + t.w > r.left and
            t.y < r.bottom and t.y + t.h > r.top)


def _resolve_x(world: World, service: CollisionService, t: Transform, body: Body) -> None:
    rect = t.as_rect()
    for solid, oneway in service.solids(world, rect):
        if oneway:
            continue
        if not _overlap(t, solid):
            continue
        # pick the shallower penetration axis: if the overlap is mostly vertical
        # (e.g. landing on the floor), leave it to the Y pass -- don't push X
        overlap_x = min(t.x + t.w, solid.right) - max(t.x, solid.left)
        overlap_y = min(t.y + t.h, solid.bottom) - max(t.y, solid.top)
        if overlap_y <= overlap_x:
            continue
        if body.vx > 0:
            t.x = solid.left - t.w
            body.on_wall_right = True
        elif body.vx < 0:
            t.x = solid.right
            body.on_wall_left = True
        body.vx = 0.0
        rect = t.as_rect()


def _resolve_y(world: World, service: CollisionService, t: Transform, body: Body) -> None:
    rect = t.as_rect()
    for solid, oneway in service.solids(world, rect):
        if not _overlap(t, solid):
            continue
        if oneway:
            if body.drop_through or body.vy <= 0:
                continue
            # only collide when the body was above the platform
            if rect.bottom - body.vy > solid.top + 2:
                continue
        if body.vy > 0:
            t.y = solid.top - t.h
            body.on_ground = True
        elif body.vy < 0:
            t.y = solid.bottom
            body.on_ceiling = True
        body.vy = 0.0
        rect = t.as_rect()


class PhysicsSystem(System):
    """Integrates gravity + velocity and resolves world collisions."""

    priority = 50

    def __init__(self, gravity: float = 2200.0) -> None:
        self.gravity = gravity

    def update(self, world: World, dt: float) -> None:
        for ent in world.query(Transform, Body):
            tr = ent.get(Transform)
            body = ent.get(Body)
            if not body.enabled:
                continue
            if body.gravity:
                body.vy += self.gravity * body.gravity_scale * dt
                if body.vy > body.max_fall:
                    body.vy = body.max_fall
            move_and_collide(world, tr, body, body.vx * dt, body.vy * dt)
