"""Engine + game tests that need no third-party test runner.

Run with::

    python -m tests.test_engine
"""

from __future__ import annotations

import os
import tempfile

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame  # noqa: E402

from vesper.engine.ecs import World  # noqa: E402
from vesper.engine.input import InputMap  # noqa: E402
from vesper.engine.physics import Body, CollisionService, PhysicsSystem, Transform  # noqa: E402
from vesper.engine.platform import Backend, Key  # noqa: E402
from vesper.engine.registry import Registry  # noqa: E402
from vesper.engine.save import SaveData, SaveManager  # noqa: E402
from vesper.engine.tilemap import TileDef, TileMap, TileSet  # noqa: E402


class FakeBackend:
    """Minimal backend that reports a fixed set of held keys."""

    name = "fake"

    def __init__(self, down=()):
        self.down = set(down)

    def pressed_keys(self):
        return set(self.down)


def test_input_binding():
    imap = InputMap(FakeBackend({Key.RIGHT, Key.Z}))
    imap.begin_frame()
    assert imap.held("right"), "right should be held"
    assert not imap.held("left")
    assert imap.held("jump")
    assert imap.axis() == 1.0
    assert imap.pressed("jump")

    imap.backend.down.clear()
    imap.begin_frame()
    assert not imap.held("right")
    assert imap.released("jump")

    imap.backend.down.add(Key.LEFT)
    imap.begin_frame()
    assert imap.axis() == -1.0


def test_platform_seam():
    """The seam must hand out a backend implementing the contract."""
    from vesper.engine.platform import create_backend
    from vesper.engine.platform.pygame_backend import PygameBackend

    backend = create_backend("pygame")
    assert isinstance(backend, Backend)
    assert isinstance(backend, PygameBackend)
    assert isinstance(backend.pressed_keys(), (set, frozenset))
    # a wrong backend name fails loudly rather than silently
    try:
        create_backend("does-not-exist")
    except ValueError:
        pass
    else:  # pragma: no cover
        raise AssertionError("unknown backend should raise")


def test_tilemap():
    ts = TileSet()
    ts.add(1, TileDef("solid", solid=True))
    ts.add(2, TileDef("crystal", solid=True, breakable=True))
    tm = TileMap(4, 4, 8, ts, fill=0)
    tm.set(1, 1, 1)
    tm.set(2, 2, 2)
    assert tm.is_solid(1, 1)
    assert not tm.is_solid(0, 0)
    assert tm.try_break(2, 2)
    assert tm.get(2, 2) == 0
    # outside the map counts as solid
    assert tm.is_solid(-1, 0)
    assert tm.is_solid(99, 0)


def test_registry():
    reg = Registry()
    reg.register("thing", "a", 1)
    assert reg.has("thing", "a")
    assert reg.get("thing", "a") == 1
    try:
        reg.register("thing", "a", 2)
    except KeyError:
        pass
    else:  # pragma: no cover
        raise AssertionError("duplicate registration should fail")
    assert reg.has("thing", "a")
    assert not reg.has("thing", "b")


def test_physics_lands_on_floor():
    pygame.init()
    pygame.display.set_mode((64, 64))
    world = World()
    service = CollisionService()
    service.add_solids(lambda w, rect: [(pygame.Rect(0, 100, 400, 20), False)])
    world.services["collision"] = service
    ent = world.create(Transform(50, 0, 16, 16), Body())
    world.add_system(PhysicsSystem(gravity=2200.0))
    for _ in range(180):
        world.update(1 / 60)
    tr = ent.get(Transform)
    assert abs((tr.y + tr.h) - 100) < 2, f"body should rest on the floor, y={tr.y}"
    assert ent.get(Body).on_ground


def test_save_roundtrip():
    with tempfile.TemporaryDirectory() as tmp:
        manager = SaveManager(tmp)
        data = SaveData(health=42, max_health=199, abilities=["dash", "charge"],
                        flags={"cores": 2})
        manager.save(data)
        assert manager.exists(0)
        loaded = manager.load(0)
        assert loaded is not None
        assert loaded.health == 42
        assert set(loaded.abilities) == {"dash", "charge"}
        assert loaded.flags["cores"] == 2
        # separate slots and erase (used by the file-select screen)
        manager.save(SaveData(health=7), 2)
        assert manager.exists(2) and not manager.exists(1)
        manager.delete(2)
        assert not manager.exists(2)
        manager.delete(9)  # erasing a missing slot is a no-op


def test_animator_advances_frames():
    """Regression: the AnimatorSystem must be running or nothing animates."""
    pygame.init()
    pygame.display.set_mode((64, 64))
    from vesper.engine.ecs import World
    from vesper.engine.render import Animation, Animator, AnimatorSystem, Sprite
    from vesper.engine.sprites import new_surface

    frames = [new_surface(6, 6, (i * 30, 0, 0)) for i in range(4)]
    world = World()
    ent = world.create(Sprite(frames[0]), Animator({"idle": Animation(frames, fps=10.0)},
                                                   "idle"))
    world.add_system(AnimatorSystem())
    seen = set()
    for _ in range(40):
        world.update(1 / 30)
        seen.add(ent.get(Animator).frame)
    assert len(seen) > 1, "animation frames must advance"
    assert ent.get(Sprite).surface in frames


def test_camera_clamps_to_room():
    """Regression: a room smaller than the viewport must still be centred on
    its own bounds (offset), not on the world origin."""
    from vesper.engine.render import Camera
    cam = Camera(512, 288)
    cam.set_bounds_rect(pygame.Rect(200, 120, 512, 288))
    cam.x, cam.y = 0, 0
    cam._clamp()
    assert cam.x == 200 and cam.y == 120, (cam.x, cam.y)
    # wider than the viewport: follow stays inside the room
    cam.set_bounds_rect(pygame.Rect(100, 120, 1968, 288))
    cam.x = 5000
    cam._clamp()
    assert cam.x == 100 + 1968 - 512, cam.x
    assert cam.y == 120, cam.y


def test_level_builds():
    from vesper.game.config import SURFACE_ONLY
    from vesper.game.level import build_level
    level = build_level()
    assert level.tilemap.width > 0
    assert level.player_spawn is not None
    assert len(level.zones) >= 1
    if not SURFACE_ONLY:
        assert any(item == "missile" for item, _, _ in level.pickups)
        assert any(name == "warden" for name, _, _ in level.enemies)
        assert len(level.gates) >= 2


def main():
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    failed = 0
    for test in tests:
        try:
            test()
            print(f"PASS {test.__name__}")
        except Exception as exc:  # pragma: no cover
            failed += 1
            import traceback
            print(f"FAIL {test.__name__}: {exc}")
            traceback.print_exc()
    print(f"\n{len(tests) - failed}/{len(tests)} passed")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
