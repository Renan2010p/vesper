# Architecture

VESPER is split into two layers that never leak into each other:

```
vesper/engine/   game-agnostic primitives (reusable)
vesper/game/     Vesper's content and rules (built on the engine)
```

The engine knows nothing about "Vesper", enemies, items or levels.  The game
knows nothing about SDL details.  This is what makes the project modular: you
can add gameplay without touching the engine, and reuse the engine for another
game.

## The platform seam

Inside the engine there is a second, equally strict split:

```
vesper/engine/platform/   the OS boundary (window, events, keys, audio,
                          fonts, files) — mirrors neko.Backend
vesper/engine/*.py        game-agnostic core (ECS, physics, scenes, registry)
```

`platform/base.py` defines the contract (`Backend`, `Event`, `EventType`,
`Key`, `WindowConfig`); `platform/pygame_backend.py` implements it;
`platform/__init__.py` is the **only** file that names a concrete backend, just
like Neko's `src/platform.zig`.  Selecting `VESPER_BACKEND` swaps it.

The core never imports pygame for OS work, and gameplay names logical
`Key`/`Event` values — never `pygame.K_*`.  Swapping pygame for an SDL3, console
or Neko backend is therefore a matter of implementing `Backend`; the ECS,
physics and rules do not change.  This is the same architecture as Neko, which
is what makes the stage-2 Zig rewrite mechanical (see
[docs/STAGES.md](STAGES.md)).

## The ECS

`vesper/engine/ecs.py` implements a small Entity-Component-System.

- **Component** — a plain data object (`@dataclass`). No behaviour.
- **Entity** — an id, a bag of components and a set of tags.
- **System** — logic. Has a `priority`; implements `update(world, dt)` and/or
  `draw(world, surface, camera)`.
- **World** — owns entities, systems and a `services` dict (registry, camera,
  audio, input, tilemap...).

Systems query by component *type*:

```python
for ent in world.query(Transform, Body):
    ...
```

Because queries are by type, a new component/system pair needs no changes to
anything else.  Entities are created through prefab functions
(`vesper/game/prefabs.py`).

## Services

Shared objects are injected via `world.services` instead of globals:

| service      | meaning                                  |
|--------------|------------------------------------------|
| `registry`   | content registry (items, enemies, ...)   |
| `input`      | `InputMap` (semantic actions)            |
| `audio`      | `Audio` (procedural sounds)              |
| `camera`     | `Camera`                                 |
| `particles`  | `ParticleSystem`                         |
| `tilemap`    | the `TileMap`                            |
| `collision`  | `CollisionService` (solid providers)     |
| `level`      | the `LevelData`                          |
| `save_callback` | persistence hook                     |

## The registry

`vesper/engine/registry.py` maps `kind/name -> object`.  The kinds used by the
game:

`item`, `weapon`, `enemy`, `ai`, `prefab`, `scene`.

Content is resolved by name at runtime, which is what makes mods possible.

## Frame flow

```
App.run()
  └─ fixed timestep (1/60)
       ├─ backend.tick(fps)                # platform: frame timing
       ├─ InputMap.begin_frame()           # platform: backend.pressed_keys()
       ├─ for event in backend.poll_events()
       │    └─ SceneManager.handle_event(event)   # platform-neutral Event
       ├─ SceneManager.update(dt)
       │    └─ Scene.update(dt) -> World.update(dt)
       │         └─ each System.update(world, dt)   # sorted by priority
       │         └─ World.flush()  -> destroy dead entities
       ├─ SceneManager.draw(canvas)
       │    └─ Scene.draw() -> background, World.draw(), HUD
       └─ backend.present(canvas)          # platform: integer-scale + flip
```

### System priorities

| priority | system                | role                                    |
|---------:|-----------------------|-----------------------------------------|
| 5        | `FloatingSystem`      | bob pickups / flyers                    |
| 14       | `GateSystem`          | open ability/cores gates                |
| 18       | `SpawnerSystem`       | periodic enemy spawns                   |
| 20       | `AISystem`            | run `ai/<behaviour>`                    |
| 20       | `PlayerControlSystem` | the whole game feel (move/jump/fire/dash/morph) |
| 30       | `ProjectileSystem`    | bullets, tile breaking, hits            |
| 40       | `CameraSystem`        | follow the player                       |
| 50       | `PhysicsSystem`       | gravity + AABB collision                |
| 55       | `StatusSystem`        | i-frames / flash                        |
| 60       | `HazardSystem`        | lava, spikes, contact damage            |
| 70       | `PickupSystem` / `SaveStationSystem` | collectibles, saving      |
| 80       | `DeathSystem`         | drops, explosions, `*_defeated` events  |
| 800/850/900/950 | tilemap, particles, sprites, foreground | drawing  |

## Physics and collision

`vesper/engine/physics.py` provides `Transform`, `Body` and `PhysicsSystem`.
*What is solid* is decided by providers registered on the `CollisionService`:

- `_tile_solids` (in `scenes/play.py`) turns solid tiles into rects.  One-way
  platforms are flagged.
- `_gate_solids` turns closed `Gate` entities into rects.

So a moving platform or a new obstacle only needs a new provider.

Movement is sub-stepped so fast bodies (dashes, missiles) cannot tunnel.

## Events

`EventBus` (`vesper/engine/events.py`) decouples systems.  Examples:
`item_collected`, `player_died`, `boss_phase`, `boss_defeated`, `gate_opened`,
`toast`.  Systems never import each other to react — they subscribe.

## Scenes

Scenes are registered under `scene/<name>` and swapped by `SceneManager`, which
also handles fades.  The `PauseScene` holds a reference to the running
`PlayScene` and resumes it with `SceneManager.set_current`, so pausing never
rebuilds the world.

## Saving

`vesper/engine/save.py` writes JSON to
`~/.local/share/vesper/save0.json`.  Only state (abilities, ammo, position,
flags) is stored — never content definitions — so saves survive content
updates and mods.
