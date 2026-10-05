# VESPER — Depths of Nara

> **An RL PROJECTS game.** Prototyped in Python/pygame (stage 1), rewritten in
> Zig on the [Neko engine](../../zig/neko) (stage 2), then shipped everywhere —
> including PlayStation 2 (stage 3). See [docs/STAGES.md](docs/STAGES.md).

A complete **metroidvania** in the spirit of classic 16-bit exploration
games: an interconnected underground world, ability-gated shortcuts, a map,
upgrades, a multi-phase boss and a save system.

You play **Vesper**, a bounty hunter who descends into the ruins of the Nara
system to stop the machine called *the Warden*.

> **100% original work.** All characters, names, artwork and audio are created
> by this project's code and are not derived from — or affiliated with — any
> existing commercial game. See [docs/LEGAL.md](docs/LEGAL.md).

## Highlights

- **Metroidvania structure** — one continuous map, eight zones, ability gates.
- **A rainy surface landing site** (Crateria-style) with your parked gunship,
  and a descent shaft into the depths.
- **Shoot-to-open hatches** — colour-coded shutter doors (any beam / missile /
  super missile) that open when shot and close behind you.
- **Exploration map** that reveals each zone as you visit it — rendered as a
  **text grid drawn with `#`** (like an ASCII dungeon map).
- **Abilities** — Missile, Charge Beam, Drone Form (morph), Grav Boots
  (double jump), Phase Dash, Mag Grip (wall jump) and Super Missile.
- **Combat** — beam, charged beam, missiles, breakable walls, multi-phase boss.
- **Enemies** with distinct AI (patrol, hover, chase, turret, jumper) and a
  data-driven spawner system.
- **HUD, area map, toasts, save/continue, phases and checkpoint respawn.**
- **Procedural art & audio** generated at runtime — zero third-party assets.
- **Extremely modular engine** — ECS + content registry + pluggable scenes, with
  a **platform seam** (`vesper/engine/platform`) so the core never touches the OS.
- **Built to be ported** — game logic names logical keys/events, never pygame
  constants, which is what makes the Zig rewrite mechanical.

## Running

```bash
python -m pip install -r requirements.txt
python main.py
```

Requires **Python 3.10+** and **pygame 2.1+** (tested on Python 3.14 /
pygame 2.6).

## Controls

| Action        | Keys                     |
|---------------|--------------------------|
| Move          | Arrow keys / WASD        |
| Aim           | Up / Down (with move = diagonal) |
| Jump / stand  | Z / Space                |
| Fire (hold = charge) | X / J            |
| Dash          | C / K                    |
| Missile (hold ↑ = Super) | V / L      |
| Morph         | Down on the ground       |
| Pause / map   | Enter / Esc / P          |
| Toggle sound  | M                        |

## Project layout

```
main.py                 entry point
vesper/rlprojects.py    studio identity + the 3-stage roadmap
vesper/engine/          reusable, game-agnostic engine
  platform/             THE SEAM: backend contract + pygame backend
  ecs.py / events.py    entities, components, systems, pub/sub bus
  physics.py/tilemap.py AABB collision and tile maps
  registry.py           content registry (moddable)
  render.py / sprites.py camera, particles, procedural surfaces
  ui.py / audio.py      immediate-mode UI, procedural audio
  save.py / scene.py    JSON saves, scene stack
vesper/game/            content and rules
  components.py         data-only components
  systems.py            rules that operate on components
  prefabs.py            entity factories (player, enemies, items, gates…)
  enemies.py / boss.py  creatures + AI behaviours
  items.py / weapons.py items and shots
  level.py              tileset + map construction
  art.py                procedural sprites
  hud.py                HUD and minimap
  scenes/               splash, title, intro, play, pause, ship, end
  content/register.py   single place that registers everything
docs/                   architecture, stages, porting and legal guides
```

## Development stages

| Stage | Tech              | Purpose                                            |
|-------|-------------------|----------------------------------------------------|
| 1     | Python + pygame   | Prototype: find the game fast *(this repository)*  |
| 2     | Zig + Neko engine | Rewrite: 100% Zig, shared engine with the studio   |
| 3     | all platforms     | Release: Linux, Windows, macOS, web and **PS2**    |

The **one rule** that keeps stage 2 cheap: game logic never touches the
platform. It uses logical keys/events from `vesper/engine/platform` and the
ECS/registry from `vesper/engine`. Only presentation and OS calls change in the
rewrite. See [docs/STAGES.md](docs/STAGES.md) and
[docs/PORTING.md](docs/PORTING.md).

## Documentation

- [docs/STAGES.md](docs/STAGES.md) — the 3-stage plan (Python → Zig/Neko → release) and the porting order.
- [docs/PORTING.md](docs/PORTING.md) — pygame → Neko cheat sheet for the stage-2 rewrite.
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) — how the engine and game fit together.
- [docs/MODDING.md](docs/MODDING.md) — add an enemy, item, weapon or map.
- [docs/LEGAL.md](docs/LEGAL.md) — how this project stays original and how to keep it that way.

## Tests and tools

```bash
python -m tests.test_engine      # engine + gameplay unit tests
python -m tools.validate_level   # proves the map is solvable and correctly gated
python -m tools.export_ascii_map # dump the whole level as a '#' text grid
```

`tools/validate_level.py` simulates the jump arc against the real tile map and
reports which pickups are reachable for each ability set.

## License

VESPER is free software licensed under the **GNU General Public License,
version 3 or later**. See [LICENSE](LICENSE).

```
Copyright (C) 2026 VESPER contributors

This program is free software: you can redistribute it and/or modify it under
the terms of the GNU General Public License as published by the Free Software
Foundation, either version 3 of the License, or (at your option) any later
version.
```
