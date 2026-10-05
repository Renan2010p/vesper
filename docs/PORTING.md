# Porting cheat sheet (pygame → Neko)

Companion to [`STAGES.md`](STAGES.md). Stage 2 rewrites the game in Zig on
[Neko](../../../zig/neko). Most of the work is mechanical if you keep stage 1's
platform seam intact: **game logic is already portable; what changes is the
presentation and the OS calls.**

Everything below maps the pygame call on the left to the Neko namespace on the
right. Signatures are in Neko's [`docs/api.md`](../../../zig/neko/docs/api.md).

## Types

| pygame / Python        | Neko / Zig                              |
|------------------------|-----------------------------------------|
| `pygame.Rect`          | `neko.Rect { x, y, w, h }` (integer)    |
| `(x, y)` tuple         | `neko.Point { x, y }` / `neko.Vec2`     |
| `(r, g, b)` / `(r,g,b,a)` | `neko.Color` (`rgb`, `rgba`, `hex`)  |
| `float` dt             | `neko.time.dt()` / `f32`                |
| `pygame.math.Vector2`  | `neko.math.Vec2` (`add`, `dot`, …)      |

## Lifecycle & loop

| pygame                          | Neko                                        |
|---------------------------------|---------------------------------------------|
| `pygame.init()`                 | `neko.screen.init(config)` / `neko.run`     |
| `pygame.display.set_mode(...)`  | `neko.window.create(...)` / config          |
| `pygame.time.Clock.tick(fps)`   | `window.begin_frame()` (dt) / `neko.time`   |
| `pygame.event.get()`            | `neko.input.poll_event()`                   |
| `pygame.display.flip()`         | `neko.screen.present()`                     |
| `pygame.quit()`                 | `neko.screen.shutdown()`                    |
| `running` loop flag             | `neko.lifecycle.keeps_running()`            |

Vesper's `engine/app.py` maps 1:1 onto Neko's `window` loop
(`begin_frame → poll_event → process → draw → present → end_frame`).

## Input & events

Stage 1 already speaks in `EventType` / `Key` (see
`vesper/engine/platform/base.py`), so this is a rename, not a redesign.

| Stage 1                         | Neko                                        |
|---------------------------------|---------------------------------------------|
| `EventType.KEYDOWN`             | `neko.Event.key_down`                       |
| `event.key == Key.M`            | `neko.input.keyDown(.m)` / `ev.key`         |
| `InputMap.held("jump")`         | `neko.input.key(.z)` (or a game-side map)   |
| `InputMap.axis()`               | game-side helper over `neko.input.key`      |
| `Backend.pressed_keys()`        | `neko.input.key(...)` per key               |

`Key.LEFT/RIGHT/UP/DOWN/RETURN/ESCAPE/SPACE/TAB` and letters map directly to
`neko.Key`; extend `neko.Key` if a binding needs a key it lacks.

## Drawing

Neko's primitive set is intentionally small. Some pygame features have no
direct equivalent and must be composed.

| pygame                                   | Neko                                     |
|------------------------------------------|------------------------------------------|
| `surface.fill(color)`                    | `neko.draw.clear(color)`                 |
| `pygame.draw.rect(s, c, r)`              | `neko.draw.rect(r, c, filled)`           |
| `pygame.draw.rect(..., width=n)`         | draw an outer rect + inner rect          |
| `pygame.draw.circle(s, c, p, r)`         | `neko.draw.circle(cx, cy, r, c, filled)` |
| `pygame.draw.line(s, c, a, b)`           | `neko.draw.line(x1, y1, x2, y2, c)`      |
| `pygame.draw.polygon(...)`               | `neko.draw.quad(...)` (convex, 4 pts)    |
| `pygame.draw.ellipse(...)`               | no primitive — compose with circles/quads|
| gradient (`vertical_gradient`)           | `neko.draw` loop, or a baked `Texture`   |
| `border_radius=...`                      | `neko.sprite.rounded(tex, …, radius, …)` |
| `pygame.transform.scale(surf, (w,h))`    | `neko.texture.draw(tex, dst, src, alpha)`|
| `pygame.transform.rotate(...)`           | `neko.texture.draw_rotated(...)`         |

### Procedural art (`art/`, `sprites.py`)

`art/` builds sprites at runtime with `pygame.Surface` + `pygame.draw`. In
stage 2:

1. render the same pixels into a CPU buffer, then
2. upload with `neko.texture.create(w, h)` + `neko.texture.update(tex, pixels, pitch)`.

This keeps the "zero third-party assets" promise: no art files ship, and the
same generator code produces the same look.

## Text & UI

| pygame                              | Neko                                      |
|-------------------------------------|-------------------------------------------|
| `pygame.font.Font(None, size)`      | `neko.text.load_font(path, size)`         |
| `font.render(text, True, color)`    | `neko.text.draw(str, x, y, .{ .color })`  |
| `draw_text(..., center=True)`       | `neko.text.Options{ .center = true }`     |
| `draw_panel` (surface + rounded)    | `neko.sprite.rounded(...)`                |
| `Menu` cursor                       | `neko.sprite.button(...)` or custom       |

Neko bundles a bitmap-font splash, so the boot card needs no font asset.

## Audio

| pygame                              | Neko                                      |
|-------------------------------------|-------------------------------------------|
| `Audio` synth (`Synth.render`)      | same maths, emit PCM bytes                 |
| `pygame.mixer.Sound(buffer=...)`    | `neko.sound.load(path)` (write PCM to a temp file) or extend the backend |
| `sound.play()`                      | `neko.sound.play(handle, loops, channel)`  |
| `set_volume`                        | `neko.sound.master_volume / sfx_volume`    |

Neko currently plays files rather than raw buffers; stage 2 either writes the
synthesised PCM to a cached file or adds a buffer entry point to the backend.

## Save / files

| Python                              | Neko                                      |
|-------------------------------------|-------------------------------------------|
| `SaveData` dataclass → JSON         | `neko.save.Writer` / `Reader` (binary)    |
| `open()` / `os.replace`             | `neko.save.write_file / read_file`        |

Keep the same field order so a port can be byte-compared against stage 1.

## Scenes

| Python                              | Neko / Godot                               |
|-------------------------------------|--------------------------------------------|
| `Scene`, `SceneManager.switch`      | `neko.scene` node tree, `window.switch_to` |
| `PauseScene` holding `PlayScene`    | `window.push_scene` / `pop_scene`          |
| `Scene.draw(surface)`               | `Node.draw`                                |

See Neko's [`godot.md`](../../../zig/neko/docs/godot.md) for the full mapping.

---

## Rule of thumb

If a line in `vesper/game/**` imports `pygame`, it is presentation and will be
rewritten. If it imports only `vesper.engine` core types, tags, components or
events, it ports almost unchanged. Audit with:

```sh
grep -rn "import pygame" vesper/game
```
