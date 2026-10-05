"""Gameplay system(s): SpawnerSystem."""

from __future__ import annotations

from ._base import *  # noqa: F401,F403


class SpawnerSystem(System):
    priority = 18

    def update(self, world: World, dt: float) -> None:
        player = world.first(tag="player")
        if player is None:
            return
        p_tr = player.get(Transform)
        for ent in world.query(Transform, Spawner):
            sp: Spawner = ent.get(Spawner)
            if not sp.active:
                continue
            tr = ent.get(Transform)
            if math.hypot(p_tr.x - tr.x, p_tr.y - tr.y) > 340:
                continue
            sp.timer -= dt
            if sp.timer > 0:
                continue
            sp.timer = sp.interval
            nearby = 0
            for other in world.query(Health, tag="enemy"):
                otr = other.get(Transform)
                if math.hypot(otr.x - tr.x, otr.y - tr.y) < sp.radius:
                    nearby += 1
            if nearby < sp.cap:
                spawn_enemy(world, sp.prefab, tr.x + random.uniform(-20, 20), tr.y)
