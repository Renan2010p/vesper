# Development stages

Vesper follows the same playbook as the studio's other game, **fnwf**:

> protótipo em Python → reescrita em Zig sobre a **Neko engine** → release em
> todas as plataformas.

The point of a fast prototype is to discover the game; the point of the Zig
rewrite is to ship it. Keeping the two stages aligned is what makes the rewrite
mechanical instead of a from-scratch second game.

- **Stage 1 — Prototype** · Python + pygame · *this repository* · fast iteration.
- **Stage 2 — Rewrite** · Zig + [Neko](../../../zig/neko) · 100% Zig, shared engine
  with the other RL PROJECTS games.
- **Stage 3 — Release** · every platform, including the **PlayStation 2**.

The current stage lives in [`vesper/rlprojects.py`](../vesper/rlprojects.py) as
`STAGE`; the boot splash shows it.

---

## Stage 1 — Prototype (Python + pygame)

Goal: nail the rules, the level design and the game feel as fast as possible.

```
main.py                     entry point
vesper/engine/              game-agnostic engine
  platform/                 THE SEAM: core never touches the OS
  ecs, events, physics,     reusable primitives
  render, tilemap, save…
vesper/game/                Vesper's content and rules
  components, systems       data + rules
  prefabs, enemies, items   content
  level, rooms, roomworld   world construction
  art, hud, ui              presentation
  scenes/                   splash, title, intro, play, pause, ship, end
vesper/rlprojects.py        studio identity + this roadmap
docs/STAGES.md              you are here
docs/PORTING.md             pygame → neko cheat sheet
```

### The one rule that keeps stage 2 cheap

**Game logic must not touch the platform.** Everything OS-facing
(window, events, keys, audio, fonts, files) goes through
`vesper/engine/platform`. Game code names logical `Key`s and `Event`s, never
`pygame.K_*` or `pygame.KEYDOWN`:

```python
from vesper.engine.platform import EventType, Key

def handle_event(self, event):
    if event.type == EventType.KEYDOWN and event.key == Key.M:
        self.app.audio.set_enabled(not self.app.audio.enabled)
```

Drawing (`pygame.draw`, `Surface`) is the *graphics backend* and is expected to
be rewritten in stage 2; [`PORTING.md`](PORTING.md) maps each call to its Neko
equivalent. Everything else is portable as-is.

---

## Stage 2 — Rewrite (Zig + Neko)

Goal: the **same game**, 100% Zig, built on Neko. `fnwf`'s
[`PARITY.md`](../../../zig/fnwf/PARITY.md) is the model: the Python build is the
*behavioural reference*; the Zig module boundaries are free to differ.

### Python → Zig module map

| Stage 1 (Python)                  | Stage 2 (Zig / Neko)                                            |
|-----------------------------------|-----------------------------------------------------------------|
| `engine/platform/*`               | `neko.platform` (seam) + `neko.screen` / `input` / `sound` / `save` |
| `engine/scene.py`                 | `neko.scene` + `neko.window` (scene stack)                      |
| `engine/ui.py`, `sprites.py`      | `neko.sprite`, `neko.text`, `neko.texture`                      |
| `engine/render.py` (camera, fx)   | `neko.draw`, `neko.effect`, `neko.render`                       |
| `engine/save.py`                  | `neko.save` (`Writer`/`Reader` + backend files)                 |
| `engine/audio.py` (synth)         | game-local synth → PCM; play via `neko.sound`                   |
| `engine/ecs.py`, `events.py`      | ported as game-local Zig (`ecs.zig`, `events.zig`) — Neko is a scene tree, so the ECS stays ours |
| `engine/physics.py`, `tilemap.py` | game-local Zig using `neko.Rect` / `neko.math.Vec2`             |
| `engine/registry.py`              | Zig comptime tables / a small registry                          |
| `game/config.py`                  | `config/constants.zig`, `config/colors.zig`                     |
| `game/i18n.py`                    | `neko.localization` + a game table                              |
| `game/art/`                       | procedural textures via `neko.texture.create/update`            |
| `game/scenes/*`                   | `states/*` (`splash`, `title`, `intro`, `gameplay`, …)          |
| `game/systems/`                   | `systems/*` (movement, combat, enemies, camera)                 |
| `game/level.py`, `rooms.py`       | `world/*`                                                       |
| `rlprojects.py`                   | `config/studio.zig`                                             |

### Porting order (dependencies first)

1. Types, math, config, RNG.
2. Save + localization (can compare bytes with stage 1).
3. Platform seam → Neko's SDL2 backend.
4. ECS + physics + tilemap.
5. Player, weapons, enemies, items (one system at a time).
6. Scenes/states and HUD.
7. Procedural art + audio.
8. Full-play parity pass against the Python build.

### Parity checklist

Legend: `[x]` done · `[~]` partial · `[ ]` todo · `n/a` out of scope.

| Area            | Stage 1 (Python) | Stage 2 (Zig) |
|-----------------|------------------|---------------|
| Platform seam   | `[x]`            | `[ ]`         |
| ECS + events    | `[x]`            | `[ ]`         |
| Physics/tilemap | `[x]`            | `[ ]`         |
| Player/combat   | `[x]`            | `[ ]`         |
| Enemies + boss  | `[x]`            | `[ ]`         |
| Level/rooms     | `[x]`            | `[ ]`         |
| Save/continue   | `[x]`            | `[ ]`         |
| i18n (pt/en)    | `[x]`            | `[ ]`         |
| HUD + map       | `[x]`            | `[ ]`         |
| Art/audio       | `[x]`            | `[ ]`         |
| Boot splash     | `[x]`            | `[ ]`         |

---

## Stage 3 — Release (all platforms)

Goal: ship. Neko already abstracts the platform, so each target is a backend +
a build recipe.

| Target            | Backend      | Notes                                             |
|-------------------|--------------|---------------------------------------------------|
| Linux             | SDL2         | AppImage / flatpak                                |
| Windows           | SDL2         | cross-compile with `zig cc`                       |
| macOS             | SDL2         | universal binary                                  |
| Web (WASM)        | SDL2 / emscripten | see fnwf's `build_web.sh`                    |
| **PlayStation 2** | **`neko` ps2** | gsKit + PS2SDK, freestanding, built with `-ofmt=c` |

The PS2 backend already exists in Neko (`src/platform/ps2/`), which is exactly
why stage 2 targets Neko instead of writing Zig from scratch.
