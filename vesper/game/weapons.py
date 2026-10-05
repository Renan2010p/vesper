"""Weapon definitions.

Weapons describe how a shot behaves; the projectile prefab is looked up by
``projectile`` name.  A new weapon is a registry entry.
"""

from __future__ import annotations

from dataclasses import dataclass

from .config import (BEAM_DAMAGE, CHARGE_DAMAGE, MISSILE_DAMAGE)


@dataclass
class WeaponDef:
    id: str
    name: str
    projectile: str
    damage: int
    speed: float
    cooldown: float
    ammo_cost: int = 0
    breaks_tiles: bool = False
    break_radius: int = 0
    shots: int = 1
    spread: float = 0.0
    charge_shot: bool = False
    sfx: str = "shoot"


def register_weapons(registry) -> None:
    weapons = [
        WeaponDef("beam", "Pulse Beam", "beam", BEAM_DAMAGE, 620.0, 0.16,
                  sfx="shoot"),
        WeaponDef("charged", "Charged Beam", "charged", CHARGE_DAMAGE, 560.0, 0.30,
                  breaks_tiles=True, break_radius=1, charge_shot=True, sfx="charged_shot"),
        WeaponDef("missile", "Missile", "missile", MISSILE_DAMAGE, 480.0, 0.42,
                  ammo_cost=1, breaks_tiles=True, break_radius=1, sfx="missile"),
        WeaponDef("super_missile", "Super Missile", "super_missile", MISSILE_DAMAGE * 3,
                  520.0, 0.6, ammo_cost=3, breaks_tiles=True, break_radius=2, sfx="missile"),
    ]
    for weapon in weapons:
        registry.register("weapon", weapon.id, weapon)
