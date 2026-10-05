"""Gameplay system(s): PickupSystem."""

from __future__ import annotations

from ._base import *  # noqa: F401,F403
from ._base import _particles, _sfx


class PickupSystem(System):
    priority = 70

    def update(self, world: World, dt: float) -> None:
        player = world.first(tag="player")
        if player is None:
            return
        prect = player.get(Transform).as_rect()
        for ent in list(world.query(Transform, Pickup)):
            pickup: Pickup = ent.get(Pickup)
            if pickup.taken:
                continue
            if not prect.colliderect(ent.get(Transform).as_rect()):
                continue
            pickup.taken = True
            item = apply_item(world, player, pickup.item_id)
            tr = ent.get(Transform)
            is_ability = item.kind == "ability"
            _sfx(world, "upgrade" if is_ability else "pickup")
            particles = _particles(world)
            if particles:
                particles.burst(tr.x + tr.w / 2, tr.y + tr.h / 2,
                                art.ITEM_COLORS.get(pickup.item_id, (255, 255, 255)), 22, 240)
            if world.events:
                world.events.emit("toast", title=t(item.name), subtitle=t(item.subtitle),
                                  kind=item.kind)
            ent.destroy()
