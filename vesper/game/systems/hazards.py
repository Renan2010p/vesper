"""Gameplay system(s): HazardSystem."""

from __future__ import annotations

from ._base import *  # noqa: F401,F403
from ._base import apply_damage


class HazardSystem(System):
    priority = 60

    def update(self, world: World, dt: float) -> None:
        tm = world.services.get("tilemap")
        player = world.first(tag="player")
        if player is None:
            return
        phealth: Health = player.get(Health)
        if phealth.dead:
            return
        ptr: Transform = player.get(Transform)

        # tile hazards (continuous, ignores i-frames)
        if tm is not None:
            total = 0.0
            for tx, ty in tm.tiles_overlapping(ptr.x + 2, ptr.y + 2, ptr.w - 4, ptr.h - 4):
                total += tm.hazard_damage(tx, ty)
            if total > 0:
                apply_damage(world, player, total * dt, ignore_invuln=True)
                player.get(Health).invuln = max(player.get(Health).invuln, 0.35)

        # contact damage
        if phealth.invuln <= 0:
            prect = ptr.as_rect()
            for enemy in world.query(Transform, ContactDamage):
                ehealth: Health = enemy.get(Health)
                if ehealth.dead:
                    continue
                etr: Transform = enemy.get(Transform)
                if prect.colliderect(etr.as_rect()):
                    contact: ContactDamage = enemy.get(ContactDamage)
                    apply_damage(world, player, contact.damage,
                                 source=(etr.x, etr.y), knockback=contact.recoil)
                    break
