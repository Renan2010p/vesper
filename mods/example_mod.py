"""Example mod: adds a healing item and a rapid-fire weapon.

This file is intentionally tiny and self-contained.  Delete or rename it if you
do not want it loaded.
"""

from __future__ import annotations

from vesper.game.components import Health
from vesper.game.items import ItemDef
from vesper.game.weapons import WeaponDef


def _heal(world, ent, loadout, health: Health) -> None:
    health.hp = min(health.max_hp, health.hp + 50)


def register(registry) -> None:
    registry.register("item", "repair_kit", ItemDef(
        "repair_kit", "REPAIR KIT", "Restores 50 energy", "tank", None, _heal))

    registry.register("weapon", "rapid", WeaponDef(
        "rapid", "Rapid Pulse", "beam", 3, 760.0, 0.08, sfx="shoot"))
