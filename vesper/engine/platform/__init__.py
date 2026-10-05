"""Platform seam — the single file that knows which backend is active.

Mirrors Neko's ``src/platform.zig``: the core imports only from here, and here
we decide which concrete backend module to instantiate.  Adding a backend
(SDL3, PS2, Neko/console) touches this module and nothing in ``core``.

Set ``VESPER_BACKEND`` to choose one at runtime; it defaults to ``pygame``.
"""

from __future__ import annotations

import os

from .base import Backend, Event, EventType, Key, SoundHandle, WindowConfig

#: Default backend; overridable with the ``VESPER_BACKEND`` env var.
BACKEND: str = os.environ.get("VESPER_BACKEND", "pygame")


def create_backend(name: str | None = None) -> Backend:
    """Instantiate the requested backend (defaults to :data:`BACKEND`)."""
    name = name or BACKEND
    if name == "pygame":
        from .pygame_backend import create

        return create()
    raise ValueError(f"unknown backend {name!r} (known: pygame)")


__all__ = [
    "Backend",
    "Event",
    "EventType",
    "Key",
    "SoundHandle",
    "WindowConfig",
    "BACKEND",
    "create_backend",
]
