# Modding guide

Everything in VESPER is content registered by name.  To add something, register
it — you never edit the engine or the existing gameplay files.

The easiest route is a file inside the top-level `mods/` package that defines
`register(registry)`; it is loaded automatically at start-up (see
`vesper/game/mods.py` and `mods/example_mod.py`).

```python
def register(registry):
    ...
```

## Add an item

```python
from vesper.game.items import ItemDef

def _effect(world, entity, loadout, health):
    loadout.abilities.add("dash")

def register(registry):
    registry.register("item", "dash", ItemDef(
        id="dash", name="PHASE DASH", subtitle="Press dash", kind="ability",
        ability="dash", apply=_effect))
```

Then place it in a level's `pickups` list (see below).

## Add a weapon

```python
from vesper.game.weapons import WeaponDef

def register(registry):
    registry.register("weapon", "spread", WeaponDef(
        id="spread", name="Spread Beam", projectile="beam", damage=6,
        speed=620, cooldown=0.3, shots=3, spread=0.3))
```

The `projectile` field picks a sprite from `vesper/game/art.py`
(`projectile_surface`).

## Add an enemy

1. Draw it (procedurally) as a function returning animations, and add it to
   `ENEMY_ART`.
2. Register an `EnemyDef`.

```python
from vesper.game.prefabs import EnemyDef
from vesper.game import art
from vesper.game.enemies import ai_patrol

def register(registry):
    registry.register("enemy", "bouncer", EnemyDef(
        name="bouncer", art=art.jumper_art, behavior="patrol",
        hp=40, contact_damage=12, w=18, h=18, speed=80,
        drops=["energy_tank"], drop_chance=0.2))
```

`behavior` refers to an AI function registered under `ai/<name>`.  Built-ins:

| behaviour | meaning                          |
|-----------|----------------------------------|
| `patrol`  | walk, turn at walls/ledges       |
| `hover`   | drift around the spawn point     |
| `chase`   | fly toward the player            |
| `turret`  | shoot at the player periodically |
| `jumper`  | hop toward the player            |
| `ambush`  | sleep, then chase                |
| `static`  | do nothing                       |

## Add an AI behaviour

```python
from vesper.engine.physics import Body

def ai_bouncer(world, entity, dt):
    body = entity.get(Body)
    if body.on_ground:
        body.vy = -520

def register(registry):
    registry.register("ai", "bouncer", ai_bouncer)
```

The signature is `(world, entity, dt)`.

## Add a scene

```python
from vesper.engine.scene import Scene

class CreditsScene(Scene):
    def draw(self, surface):
        surface.fill((0, 0, 0))

def register(registry):
    registry.register("scene", "credits", CreditsScene)
```

Switch with `app.switch_scene("credits")`.

## Add / edit a map

The world lives in `vesper/game/level.py`.  It is built from a tiny DSL:

```python
b.carve(x, y, w, h)              # hollow out a room (empty tiles)
b.solid(x, y, w, h, tile)        # fill with a solid tile
b.platform(x, y, w)              # one-way platform
b.hazard_row(x, y, w, tile)      # spikes / lava row
```

Then list placements as plain data:

```python
enemies = [("crawler", 26, 100), ...]        # (enemy, tile_x, tile_y)
pickups = [("missile", 92, 69), ...]         # (item, tile_x, tile_y)
gates = [{"x": ..., "required": "charge"}]   # or {"cores_needed": 2}
saves = [px(10, 100), ...]
spawners = [{"prefab": "flyer", "x": ..., "y": ..., "interval": 6,
             "cap": 3, "radius": 160}]
```

Coordinates are in **tiles**; `px(tx, ty)` converts to pixel centres.

### Tiles

Tiles are `TileDef`s added in `build_tileset()`.  A tile can be `solid`,
`hazard`, `breakable`, `oneway`, `foreground`, and carry `tags`.  Add a new
tile by adding a `TileDef`; the renderer generates its sprite automatically.

## ASCII maps (level grids in Python)

Levels are plain-text grids drawn with `#`, declared in
`vesper/game/rooms.py` as **lists of rows**.  No external `.txt` file is needed:

```python
NARA_SURFACE = [
    "########################",
    "#        NNNNN         #",
    "#        =====         #",
    "########################",
]
```

Each room ties a grid to its zone, exits, enemies and items:

```python
ROOMS = {
    "landing": {
        "label": "zone.surface",
        "zone": "surface",
        "grid": NARA_SURFACE,
        "exits": {"left": {"to": "cave", "enter": "right"}},
    },
}
```

`vesper/game/roomworld.py` parses the grid into a tile map.  Edit `rooms.py`
and restart the game to see your changes.

Tile characters:

| char | meaning            |
|------|--------------------|
| `#`  | wall (surface rock)|
| `.` / space | empty      |
| `=`  | one-way ledge      |
| `^`  | spikes             |
| `~`  | lava               |
| `%`  | breakable wall     |
| `,`  | moss / decoration  |

Marker characters (the tile under them is left empty):

| char | meaning                          |
|------|----------------------------------|
| `N`  | gunship (a run sets its centre)  |
| `|`  | vertical hatch (run = height)    |
| `-`  | horizontal hatch (run = width)   |
| `D`  | single hatch                     |
| `@`  | player spawn                     |
| `S`  | save station                     |
| `M` `C` `W` `G` `H` `K` `T` `X` | item pickups (missile, charge, morph, grav boots, dash, mag grip, energy tank, missile tank) |

The grid is stamped into the room's local tilemap.  `python -m
tools.export_ascii_map` dumps a built room back out in the same character set
(and its default `nara_map.txt` output is git-ignored).

## Tips

- Keep content registration idempotent-ish: the registry rejects duplicate
  names, so guard with `registry.has(kind, name)` if a mod may load twice.
- Prefer emitting/listening to events over importing other systems.
- Never put behaviour in a component; put it in a system.
