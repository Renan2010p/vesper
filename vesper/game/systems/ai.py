"""Gameplay system(s): AISystem."""

from __future__ import annotations

from ._base import *  # noqa: F401,F403
from ._base import _registry


class AISystem(System):
    priority = 20

    def update(self, world: World, dt: float) -> None:
        registry = _registry(world)
        for ent in world.query(AI):
            if ent.has(Health) and ent.get(Health).dead:
                continue
            ai: AI = ent.get(AI)
            if not registry.has("ai", ai.behavior):
                continue
            registry.get("ai", ai.behavior)(world, ent, dt)
