"""Single entry point that wires all built-in content into the registry.

``register_all`` is idempotent and is the only function the engine calls.  To
add a mod, call the mod's ``register(registry)`` helper here (or from a plugin
module) -- the rest of the engine stays untouched.
"""

from __future__ import annotations


def register_all(app) -> None:
    if app.runtime.get("content_registered"):
        return
    registry = app.registry

    from .. import boss, enemies, items, prefabs, weapons
    from ..scenes import register_scenes

    items.register_items(registry)
    weapons.register_weapons(registry)
    prefabs.register_prefabs(registry)
    enemies.register_enemies(registry)
    boss.register_boss(registry)
    register_scenes(registry)

    from ..mods import load_mods
    app.runtime["mods"] = load_mods(registry)

    app.runtime["content_registered"] = True
