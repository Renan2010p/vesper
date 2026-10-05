"""Gameplay system(s): GateSystem."""

from __future__ import annotations

from ._base import *  # noqa: F401,F403
from ._base import _particles, _sfx


class GateSystem(System):
    priority = 14

    def update(self, world: World, dt: float) -> None:
        player = world.first(tag="player")
        loadout: Loadout | None = player.get(Loadout) if player else None
        for ent in world.query(Gate):
            gate: Gate = ent.get(Gate)
            if gate.open:
                continue
            unlocked = False
            if loadout is not None:
                if gate.required and loadout.has(gate.required):
                    unlocked = True
                if gate.cores_needed and loadout.cores >= gate.cores_needed:
                    unlocked = True
            if unlocked:
                gate.open = True
                tr = ent.get(Transform)
                _sfx(world, "door")
                particles = _particles(world)
                if particles:
                    particles.burst(tr.x + tr.w / 2, tr.y + tr.h / 2, (150, 240, 255), 26, 240)
                opened = world.services.get("gate_art", {}).get(ent.id)
                if opened is not None:
                    ent.get(Sprite).surface = opened
                if world.events:
                    world.events.emit("gate_opened", gate=gate)
