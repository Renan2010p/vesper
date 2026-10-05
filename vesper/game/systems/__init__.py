"""Gameplay systems, split by concern.

Each system owns one concern (control, AI, projectiles, damage, pickups...).
They communicate through the ECS and the event bus, never by calling each
other, so they can be reordered, replaced or extended independently.
"""

from __future__ import annotations

from ._base import apply_damage
from .floating import FloatingSystem
from .gates import GateSystem
from .doors import DoorSystem
from .ai import AISystem
from .control import PlayerControlSystem
from .projectiles import ProjectileSystem
from .hazards import HazardSystem
from .status import StatusSystem
from .pickups import PickupSystem
from .save_stations import SaveStationSystem
from .ship import ShipSystem
from .spawners import SpawnerSystem
from .death import DeathSystem
from .camera import CameraSystem
from .tilemap_draw import TileMapDrawSystem, TileMapForegroundSystem

__all__ = [
    "apply_damage",
    "FloatingSystem",
    "GateSystem",
    "DoorSystem",
    "AISystem",
    "PlayerControlSystem",
    "ProjectileSystem",
    "HazardSystem",
    "StatusSystem",
    "PickupSystem",
    "SaveStationSystem",
    "ShipSystem",
    "SpawnerSystem",
    "DeathSystem",
    "CameraSystem",
    "TileMapDrawSystem",
    "TileMapForegroundSystem",
]
