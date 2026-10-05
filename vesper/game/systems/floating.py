"""Gameplay system(s): FloatingSystem."""

from __future__ import annotations

from ._base import *  # noqa: F401,F403


class FloatingSystem(System):
    priority = 5

    def update(self, world: World, dt: float) -> None:
        for ent in world.query(Transform, Floating):
            fl: Floating = ent.get(Floating)
            tr: Transform = ent.get(Transform)
            fl.phase += dt * fl.speed
            tr.y = fl.base_y + math.sin(fl.phase) * fl.amplitude
