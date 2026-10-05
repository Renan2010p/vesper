"""Gameplay system(s): DeathSystem."""

from __future__ import annotations

from ._base import *  # noqa: F401,F403
from ._base import _particles, _sfx


class DeathSystem(System):
    priority = 80

    def update(self, world: World, dt: float) -> None:
        for ent in list(world.query(Health)):
            health: Health = ent.get(Health)
            if not health.dead:
                continue
            tr = ent.get(Transform)
            if ent.has_tag("player"):
                if world.events:
                    world.events.emit("player_died")
                health.dead = False  # scene decides; avoid repeat emits each frame
                continue
            # enemy death
            is_boss = ent.has_tag("boss")
            particles = _particles(world)
            if particles:
                particles.burst(tr.x + tr.w / 2, tr.y + tr.h / 2,
                                (255, 160, 90), 40 if is_boss else 16,
                                420 if is_boss else 240)
            _sfx(world, "explode" if is_boss else "enemy_die")
            drops: Drops | None = ent.get(Drops)
            if drops and drops.items and random.random() < drops.chance:
                item_id = random.choice(drops.items)
                spawn_pickup(world, item_id, tr.x + tr.w / 2, tr.y + tr.h / 2)
            if is_boss and world.events:
                world.events.emit("boss_defeated")
            world.services["kill_count"] = world.services.get("kill_count", 0) + 1
            world.services.get("enemy_defs", {}).pop(ent.id, None)
            ent.destroy()
