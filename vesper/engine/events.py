"""A minimal publish/subscribe event bus.

Systems stay decoupled by talking through events instead of importing each
other.  For example the damage system emits ``entity.died`` and the loot system
listens for it, without either knowing the other exists.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any, Callable, DefaultDict, List


class EventBus:
    def __init__(self) -> None:
        self._subs: DefaultDict[str, List[Callable]] = defaultdict(list)
        self._queue: List[tuple] = []

    def on(self, name: str, fn: Callable) -> Callable:
        self._subs[name].append(fn)
        return fn

    def off(self, name: str, fn: Callable) -> None:
        if fn in self._subs.get(name, []):
            self._subs[name].remove(fn)

    def emit(self, name: str, **payload: Any) -> None:
        """Publish immediately to every listener."""
        for fn in list(self._subs.get(name, ())):
            fn(**payload)

    def post(self, name: str, **payload: Any) -> None:
        """Queue an event to be flushed at the end of the frame."""
        self._queue.append((name, payload))

    def flush(self) -> None:
        queue, self._queue = self._queue, []
        for name, payload in queue:
            self.emit(name, **payload)

    def clear(self) -> None:
        self._subs.clear()
        self._queue.clear()
