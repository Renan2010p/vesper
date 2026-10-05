"""Items and their effects.

An item is pure data plus an ``apply`` handler.  Pickups reference items by id,
so a mod can add a new collectible by registering it here and placing it in a
level.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Optional

from .components import Health, Loadout
from .config import ENERGY_PER_TANK, MISSILES_PER_TANK


@dataclass
class ItemDef:
    id: str
    name: str
    subtitle: str
    kind: str = "ability"          # ability | tank | core | utility
    ability: Optional[str] = None
    apply: Optional[Callable] = None


# -- effect handlers --------------------------------------------------------

def _energy_tank(world, ent, loadout: Loadout, health: Health) -> None:
    loadout.energy_tanks += 1
    health.max_hp += ENERGY_PER_TANK
    health.hp = health.max_hp


def _missile_tank(world, ent, loadout: Loadout, health: Health) -> None:
    loadout.missile_tanks += 1
    loadout.max_missiles += MISSILES_PER_TANK
    loadout.missiles = loadout.max_missiles


def _grant(ability: str, *, ammo: int = 0, missiles: int = 0):
    def handler(world, ent, loadout: Loadout, health: Health) -> None:
        loadout.abilities.add(ability)
        if ammo:
            loadout.max_missiles += ammo
            loadout.missiles = loadout.max_missiles
        if missiles and loadout.max_missiles == 0:
            loadout.max_missiles = 5
            loadout.missiles = 5
    return handler


def _core(world, ent, loadout: Loadout, health: Health) -> None:
    loadout.cores += 1
    if world.events:
        world.events.emit("core_collected", count=loadout.cores)


def register_items(registry) -> None:
    items = [
        ItemDef("energy_tank", "item.energy_tank", "item.energy_tank.desc",
                "tank", None, _energy_tank),
        ItemDef("missile_tank", "item.missile_tank", "item.missile_tank.desc",
                "tank", None, _missile_tank),
        ItemDef("missile", "item.missile", "item.missile.desc",
                "ability", "missile", _grant("missile", ammo=MISSILES_PER_TANK)),
        ItemDef("charge", "item.charge", "item.charge.desc",
                "ability", "charge", _grant("charge")),
        ItemDef("morph", "item.morph", "item.morph.desc",
                "ability", "morph", _grant("morph")),
        ItemDef("grav_boots", "item.grav_boots", "item.grav_boots.desc",
                "ability", "grav_boots", _grant("grav_boots")),
        ItemDef("dash", "item.dash", "item.dash.desc",
                "ability", "dash", _grant("dash")),
        ItemDef("wall_grip", "item.wall_grip", "item.wall_grip.desc",
                "ability", "wall_grip", _grant("wall_grip")),
        ItemDef("super_missile", "item.super_missile", "item.super_missile.desc",
                "ability", "super_missile",
                _grant("super_missile", ammo=MISSILES_PER_TANK)),
        ItemDef("core", "item.core", "item.core.desc",
                "core", None, _core),
        ItemDef("map", "item.map", "item.map.desc",
                "utility", None, lambda w, e, l, h: l.items.add("map")),
    ]
    for item in items:
        registry.register("item", item.id, item)


def apply_item(world, ent, item_id: str):
    """Apply an item's effect to the player entity. Returns the ItemDef."""
    registry = world.services["registry"]
    item: ItemDef = registry.get("item", item_id)
    loadout = ent.get(Loadout)
    health = ent.get(Health)
    loadout.items.add(item_id)
    if item.apply:
        item.apply(world, ent, loadout, health)
    if world.events:
        world.events.emit("item_collected", item=item)
    return item
