"""Action-based input, decoupled from any keyboard library.

Gameplay code never touches raw key constants: it asks for semantic actions
(``left``, ``jump``, ``fire``...).  Keys are logical :class:`~vesper.engine.platform.Key`
values, so the same bindings work on SDL, a console pad or a future Neko
backend.  Rebind at runtime through :meth:`InputMap.bind`, or load a profile
from a dict.  Several key sets can be active at once (arrows *and* WASD by
default).
"""

from __future__ import annotations

from typing import Dict, Iterable, List, Optional, Set

from .platform import Backend, Key

DEFAULT_PROFILE: Dict[str, List[Key]] = {
    "left": [Key.LEFT, Key.A],
    "right": [Key.RIGHT, Key.D],
    "up": [Key.UP, Key.W],
    "down": [Key.DOWN, Key.S],
    "jump": [Key.Z, Key.SPACE],
    "fire": [Key.X, Key.J],
    "dash": [Key.C, Key.K],
    "ability": [Key.V, Key.L],
    "pause": [Key.RETURN, Key.ESCAPE, Key.P],
    "confirm": [Key.RETURN, Key.Z, Key.SPACE],
    "cancel": [Key.ESCAPE, Key.X],
}


class InputMap:
    def __init__(self, backend: Optional[Backend] = None,
                 profile: Dict[str, Iterable[Key]] | None = None) -> None:
        self.backend = backend
        self.bindings: Dict[str, List[Key]] = {}
        self.held_keys: Set[Key] = set()
        self._prev_keys: Set[Key] = set()
        self.load(profile or DEFAULT_PROFILE)

    def load(self, profile: Dict[str, Iterable[Key]]) -> None:
        self.bindings = {action: list(keys) for action, keys in profile.items()}

    def bind(self, action: str, *keys: Key) -> None:
        self.bindings[action] = list(keys)

    # -- frame lifecycle --------------------------------------------------
    def begin_frame(self) -> None:
        self._prev_keys = self.held_keys
        if self.backend is None:
            return
        self.held_keys = set(self.backend.pressed_keys())

    def end_frame(self) -> None:
        pass

    # -- queries ----------------------------------------------------------
    def held(self, action: str) -> bool:
        return any(k in self.held_keys for k in self.bindings.get(action, ()))

    def pressed(self, action: str) -> bool:
        keys = self.bindings.get(action, ())
        return any(k in self.held_keys and k not in self._prev_keys for k in keys)

    def released(self, action: str) -> bool:
        keys = self.bindings.get(action, ())
        return any(k not in self.held_keys and k in self._prev_keys for k in keys)

    def axis(self, negative: str = "left", positive: str = "right") -> float:
        return (1.0 if self.held(positive) else 0.0) - (1.0 if self.held(negative) else 0.0)

    def vertical_axis(self) -> float:
        return (1.0 if self.held("down") else 0.0) - (1.0 if self.held("up") else 0.0)
