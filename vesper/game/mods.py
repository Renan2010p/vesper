"""Mod loader.

Any module inside the top-level ``mods`` package that exposes a
``register(registry)`` function is loaded automatically at start-up.  Mods use
exactly the same extension points as the built-in content, so there is no
privileged API.
"""

from __future__ import annotations

import importlib
import pkgutil
from typing import List


def load_mods(registry) -> List[str]:
    loaded: List[str] = []
    try:
        import mods  # type: ignore
    except ImportError:
        return loaded
    for info in pkgutil.iter_modules(mods.__path__):
        if info.name.startswith("_"):
            continue
        module = importlib.import_module(f"mods.{info.name}")
        register = getattr(module, "register", None)
        if callable(register):
            register(registry)
            loaded.append(info.name)
    return loaded
