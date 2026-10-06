"""Gameplay components.

Components hold data only.  Every behaviour lives in ``systems.py``.  Because
systems address components by type, a mod can introduce a new component and a
matching system without touching the core.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Set, Tuple


@dataclass
class Health:
    hp: int = 99
    max_hp: int = 99
    team: str = "player"          # "player" | "enemy"
    invuln: float = 0.0
    flash: float = 0.0
    dead: bool = False


@dataclass
class ContactDamage:
    damage: int = 8
    recoil: float = 240.0


@dataclass
class Projectile:
    damage: int = 5
    team: str = "player"
    owner: int = 0
    lifetime: float = 2.2
    breaks_tiles: bool = False
    break_radius: int = 0
    pierce: int = 0
    tier: int = 0
    knockback: float = 0.0
    gravity: float = 0.0
    homing: float = 0.0


@dataclass
class Player:
    facing: int = 1
    aim: str = "side"             # side/up/down/updiag/downdiag
    jumps_left: int = 1
    coyote: float = 0.0
    jump_buffer: float = 0.0
    dash_timer: float = 0.0
    dash_cd: float = 0.0
    dash_dir: int = 1
    charge: float = 0.0
    charging: bool = False
    fire_cd: float = 0.0
    wall_sliding: bool = False
    morph: bool = False
    morph_lock: float = 0.0
    hurt_timer: float = 0.0
    land_timer: float = 0.0
    was_ground: bool = True
    respawn: Tuple[float, float] = (0.0, 0.0)


@dataclass
class Loadout:
    """Abilities, ammo and collectible counts for the heroine."""

    abilities: Set[str] = field(default_factory=set)
    items: Set[str] = field(default_factory=set)
    missiles: int = 0
    max_missiles: int = 0
    energy_tanks: int = 0
    missile_tanks: int = 0
    cores: int = 0

    def has(self, ability: str) -> bool:
        return ability in self.abilities


@dataclass
class AI:
    behavior: str = "patrol"
    state: Dict[str, Any] = field(default_factory=dict)
    timer: float = 0.0
    origin: Tuple[float, float] = (0.0, 0.0)
    range: float = 0.0
    cooldown: float = 0.0


@dataclass
class Pickup:
    item_id: str = "energy_tank"
    amount: int = 1
    bob: float = 0.0
    taken: bool = False


@dataclass
class Gate:
    required: str = "missile"     # ability name or special "cores"
    cores_needed: int = 0
    open: bool = False
    opening: float = 0.0
    label: str = ""


@dataclass
class SaveStation:
    used: bool = False


@dataclass
class Boss:
    phase: int = 0
    pattern: int = 0
    timer: float = 0.0
    shot_cd: float = 0.0
    home_y: float = 0.0
    home_x: float = 0.0
    active: bool = False
    intro: float = 0.0
    fleeing: bool = False
    flee_timer: float = 0.0


@dataclass
class Spawner:
    """Periodically spawns a prefab until a nearby cap is reached."""

    prefab: str = "flyer"
    interval: float = 4.0
    cap: int = 3
    timer: float = 0.0
    radius: float = 120.0
    active: bool = True


@dataclass
class Floating:
    """Bobbing/hover helper so system code stays declarative."""

    amplitude: float = 4.0
    speed: float = 2.0
    phase: float = 0.0
    base_y: float = 0.0


@dataclass
class Drops:
    items: list = field(default_factory=list)
    chance: float = 1.0


@dataclass
class Door:
    """A sensor hatch: opens on contact and closes when the player leaves."""

    tier: int = 0                    # 0=any beam/contact, 1=missile, 2=super missile
    axis: str = "h"                  # "h" horizontal barrier, "v" vertical
    open: bool = False
    open_timer: float = 0.0          # time left before it closes
    anim: float = 0.0                # 0 closed .. 1 fully open
    target: str = ""                 # room to load when passing through
    enter: str = ""                  # which side to appear on in the target room


@dataclass
class Ship:
    """Vesper's gunship: a boardable save/refuel point."""

    entrance_w: float = 64.0
    entrance_h: float = 42.0
    phase: float = 0.0
    hover: bool = True


@dataclass
class Lifetime:
    remaining: float = 30.0
    destroy_flash: bool = False


@dataclass
class Nametag:
    name: str = ""


@dataclass
class Forms:
    """Alternate animation sets/sizes for shape-shifting entities."""

    human_anims: dict = field(default_factory=dict)
    morph_anims: dict = field(default_factory=dict)
    human_size: Tuple[float, float] = (14.0, 22.0)
    morph_size: Tuple[float, float] = (14.0, 14.0)
