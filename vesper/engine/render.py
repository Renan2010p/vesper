"""Rendering primitives: camera, sprites, animation and particles."""

from __future__ import annotations

import math
import random
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import pygame

from .ecs import System, World
from .physics import Transform


class Camera:
    """A clamped, smoothly following camera with screen shake."""

    def __init__(self, viewport_w: int, viewport_h: int) -> None:
        self.x = 0.0
        self.y = 0.0
        self.viewport_w = viewport_w
        self.viewport_h = viewport_h
        self.bounds: Optional[pygame.Rect] = None
        self._shake = 0.0
        self._shake_time = 0.0
        self._shaking = 0.0
        self.lerp = 0.18

    def set_bounds_rect(self, rect) -> None:
        """Limit the view to an arbitrary world-space rectangle (one room)."""
        self.bounds = pygame.Rect(rect)

    def snap(self, tx: float, ty: float) -> None:
        self.x = tx - self.viewport_w / 2
        self.y = ty - self.viewport_h / 2
        self._clamp()

    def follow(self, tx: float, ty: float, dt: float, lookahead: float = 0.0) -> None:
        target_x = tx - self.viewport_w / 2 + lookahead
        target_y = ty - self.viewport_h / 2
        factor = 1.0 - math.pow(1.0 - self.lerp, dt * 60.0)
        self.x += (target_x - self.x) * factor
        self.y += (target_y - self.y) * factor
        self._clamp()

    def shake(self, magnitude: float, duration: float = 0.25) -> None:
        self._shake = max(self._shake, magnitude)
        self._shake_time = max(self._shake_time, duration)
        self._shaking = self._shake_time

    def update(self, dt: float) -> None:
        if self._shake_time > 0:
            self._shake_time -= dt
            if self._shake_time <= 0:
                self._shake = 0.0

    def _clamp(self) -> None:
        if self.bounds is not None:
            if self.bounds.width <= self.viewport_w:
                self.x = self.bounds.left + (self.bounds.width - self.viewport_w) / 2
            else:
                self.x = max(self.bounds.left, min(self.x, self.bounds.right - self.viewport_w))
            if self.bounds.height <= self.viewport_h:
                self.y = self.bounds.top + (self.bounds.height - self.viewport_h) / 2
            else:
                self.y = max(self.bounds.top, min(self.y, self.bounds.bottom - self.viewport_h))

    @property
    def offset(self) -> Tuple[int, int]:
        ox, oy = self.x, self.y
        if self._shake_time > 0:
            ox += random.uniform(-self._shake, self._shake)
            oy += random.uniform(-self._shake, self._shake)
        return int(-ox), int(-oy)

    def view_rect(self) -> pygame.Rect:
        return pygame.Rect(int(self.x), int(self.y), self.viewport_w, self.viewport_h)


# ---------------------------------------------------------------------------
# Sprites & animation
# ---------------------------------------------------------------------------

@dataclass
class Sprite:
    surface: pygame.Surface
    offset: Tuple[float, float] = (0.0, 0.0)
    layer: int = 0
    flip_x: bool = False
    visible: bool = True
    alpha: int = 255


@dataclass
class Animation:
    frames: List[pygame.Surface]
    fps: float = 10.0
    loop: bool = True
    next_: Optional[str] = None

    def duration(self) -> float:
        return len(self.frames) / self.fps if self.fps else 0.0


class Animator:
    def __init__(self, animations: Dict[str, Animation], current: str) -> None:
        self.animations = animations
        self.current = current
        self.time = 0.0
        self.frame = 0
        self.finished = False

    def play(self, name: str, restart: bool = False) -> None:
        if name == self.current and not restart:
            return
        if name not in self.animations:
            return
        self.current = name
        self.time = 0.0
        self.frame = 0
        self.finished = False

    def update(self, sprite: Sprite, dt: float) -> None:
        anim = self.animations.get(self.current)
        if anim is None or not anim.frames:
            return
        self.time += dt
        step = 1.0 / anim.fps if anim.fps else 1.0
        while self.time >= step:
            self.time -= step
            self.frame += 1
            if self.frame >= len(anim.frames):
                if anim.loop:
                    self.frame = 0
                else:
                    self.frame = len(anim.frames) - 1
                    self.finished = True
                    if anim.next_:
                        self.play(anim.next_)
                    break
        sprite.surface = anim.frames[self.frame]


class AnimatorSystem(System):
    priority = 10

    def update(self, world: World, dt: float) -> None:
        for ent in world.query(Sprite, Animator):
            ent.get(Animator).update(ent.get(Sprite), dt)


class SpriteDrawSystem(System):
    """Draws every entity that has a Transform + Sprite, sorted by layer."""

    priority = 900

    def __init__(self, layer: Optional[int] = None) -> None:
        #: if set, only draw entities whose sprite.layer == layer
        self.layer = layer

    def draw(self, world: World, surface: pygame.Surface, camera: Camera) -> None:
        drawables = []
        for ent in world.query(Sprite):
            sprite = ent.get(Sprite)
            if not sprite.visible:
                continue
            if self.layer is not None and sprite.layer != self.layer:
                continue
            transform = ent.get(Transform)
            if transform is None:
                continue
            drawables.append((sprite.layer, transform.y, sprite, transform))
        drawables.sort(key=lambda item: (item[0], item[1]))
        ox, oy = camera.offset
        screen = surface.get_rect()
        for _layer, _y, sprite, transform in drawables:
            surf = sprite.surface
            if sprite.flip_x:
                surf = pygame.transform.flip(surf, True, False)
            if sprite.alpha != 255:
                surf = surf.copy()
                surf.set_alpha(sprite.alpha)
            pos = (int(transform.x + sprite.offset[0]) + ox,
                   int(transform.y + sprite.offset[1]) + oy)
            if screen.colliderect(pygame.Rect(pos, surf.get_size())):
                surface.blit(surf, pos)


# ---------------------------------------------------------------------------
# Particles
# ---------------------------------------------------------------------------

@dataclass
class Particle:
    x: float
    y: float
    vx: float
    vy: float
    life: float
    max_life: float
    color: Tuple[int, int, int]
    radius: float = 2.0
    gravity: float = 0.0
    shrink: bool = True


class ParticleSystem(System):
    priority = 850

    def __init__(self, limit: int = 600) -> None:
        self.particles: List[Particle] = []
        self.limit = limit

    def spawn(self, x, y, count=8, color=(220, 220, 240), speed=120.0, life=0.5,
              radius=2.0, gravity=0.0, spread=None, angle=None) -> None:
        for _ in range(count):
            if len(self.particles) >= self.limit:
                break
            if angle is None:
                a = random.uniform(0, math.tau) if spread is None else random.uniform(-spread, spread)
            else:
                a = angle + (random.uniform(-spread, spread) if spread else 0.0)
            spd = random.uniform(speed * 0.3, speed)
            lf = random.uniform(life * 0.6, life)
            self.particles.append(Particle(
                x, y, math.cos(a) * spd, math.sin(a) * spd, lf, lf,
                color, radius, gravity))

    def burst(self, x, y, color, count=12, speed=180.0) -> None:
        self.spawn(x, y, count=count, color=color, speed=speed, life=0.6, radius=2.5, gravity=300)

    def update(self, world: World, dt: float) -> None:
        alive = []
        for p in self.particles:
            p.life -= dt
            if p.life <= 0:
                continue
            p.vy += p.gravity * dt
            p.x += p.vx * dt
            p.y += p.vy * dt
            alive.append(p)
        self.particles = alive

    def draw(self, world: World, surface: pygame.Surface, camera: Camera) -> None:
        ox, oy = camera.offset
        for p in self.particles:
            t = max(0.0, p.life / p.max_life)
            radius = p.radius * (t if p.shrink else 1.0)
            if radius < 0.5:
                continue
            color = (min(255, int(p.color[0] * t + 20)),
                     min(255, int(p.color[1] * t + 20)),
                     min(255, int(p.color[2] * t + 20)))
            pygame.draw.circle(surface, color, (int(p.x) + ox, int(p.y) + oy),
                               max(1, int(radius)))
