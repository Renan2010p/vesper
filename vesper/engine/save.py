"""JSON save games.

The save file stores only *state* (flags, inventory, position), never content
definitions, so it survives content updates and mods.  A version field is kept
for forward migration.
"""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, field
from typing import Any, Dict

SAVE_VERSION = 1


@dataclass
class SaveData:
    version: int = SAVE_VERSION
    slot: int = 0
    play_time: float = 0.0
    spawn_zone: str = "landing"
    spawn_x: float = 0.0
    spawn_y: float = 0.0
    health: int = 99
    max_health: int = 99
    missiles: int = 0
    max_missiles: int = 0
    abilities: list = field(default_factory=list)
    items: list = field(default_factory=list)
    flags: Dict[str, Any] = field(default_factory=dict)
    visited: Dict[str, Any] = field(default_factory=dict)
    kills: int = 0

    def to_json(self) -> str:
        return json.dumps(asdict(self), indent=2)

    @classmethod
    def from_json(cls, text: str) -> "SaveData":
        raw = json.loads(text)
        known = {f for f in cls.__dataclass_fields__}  # type: ignore[attr-defined]
        return cls(**{k: v for k, v in raw.items() if k in known})


class SaveManager:
    def __init__(self, directory: str | None = None) -> None:
        self.directory = directory or os.path.join(
            os.path.expanduser("~"), ".local", "share", "vesper")
        os.makedirs(self.directory, exist_ok=True)

    def path_for(self, slot: int = 0) -> str:
        return os.path.join(self.directory, f"save{slot}.json")

    def exists(self, slot: int = 0) -> bool:
        return os.path.isfile(self.path_for(slot))

    def save(self, data: SaveData, slot: int = 0) -> str:
        data.slot = slot
        path = self.path_for(slot)
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            fh.write(data.to_json())
        os.replace(tmp, path)
        return path

    def load(self, slot: int = 0) -> SaveData | None:
        path = self.path_for(slot)
        if not os.path.isfile(path):
            return None
        try:
            with open(path, "r", encoding="utf-8") as fh:
                return SaveData.from_json(fh.read())
        except (OSError, ValueError):
            return None

    def delete(self, slot: int = 0) -> None:
        """Erase a save file (used by the file-select screen)."""
        try:
            os.remove(self.path_for(slot))
        except OSError:
            pass
