"""Level reachability validator.

Approximates the player's jump (rise vertically, travel at the apex, drop onto
the target) and walks the platform graph from the spawn, respecting solid
walls, breakable crystal (passable once you have the Missile), and ability
gates.  It then reports which pickups are reachable per ability set -- a quick
way to prove the level is solvable and correctly gated.

Run with::

    python -m tools.validate_level
"""

from __future__ import annotations

import math
from typing import Dict, List

import pygame

from vesper.game.level import T_CRYSTAL, T_ONEWAY, build_level

TS = 24
V = 700.0        # jump speed
G = 2200.0       # gravity
RUN = 190.0      # run speed


def jump_horizontal(rise: float):
    if rise <= 0:
        drop = min(-rise, 2000)
        t = math.sqrt(2 * drop / G) if drop > 0 else 0.5
        return RUN * (t + 0.3)
    disc = V * V - 2 * G * rise
    if disc < 0:
        return None
    return RUN * (V + math.sqrt(disc)) / G


def double_jump_horizontal(rise: float):
    single = jump_horizontal(min(rise, 111))
    if single is None:
        return None
    if rise <= 111:
        return max(single, jump_horizontal(rise))
    rem = rise - 111
    disc = 644 * 644 - 2 * G * rem
    if disc < 0:
        return None
    return RUN * (0.318 + (644 + math.sqrt(disc)) / G)


def surfaces(tm):
    runs: List[dict] = []
    for y in range(tm.height):
        x = 0
        while x < tm.width:
            if tm.get(x, y) == T_ONEWAY:
                x0 = x
                while x < tm.width and tm.get(x, y) == T_ONEWAY:
                    x += 1
                runs.append({"x0": x0 * TS, "x1": x * TS, "y": y * TS})
            else:
                x += 1
    for y in range(1, tm.height):
        x = 0
        while x < tm.width:
            solid = tm.tileset[tm.get(x, y)].solid
            above = tm.tileset[tm.get(x, y - 1)].solid
            if solid and not above:
                x0 = x
                while x < tm.width:
                    s = tm.tileset[tm.get(x, y)].solid
                    a = tm.tileset[tm.get(x, y - 1)].solid
                    if not (s and not a):
                        break
                    x += 1
                runs.append({"x0": x0 * TS, "x1": x * TS, "y": y * TS})
            else:
                x += 1
    return runs


def make_blocker(level):
    gates = []
    for spec in level.gates:
        rect = pygame.Rect(spec["x"], spec["y"], spec["w"], spec["h"])
        gates.append((rect, spec.get("required"), spec.get("cores_needed", 0)))

    def blocked(px, py, tm, abilities):
        for rect, required, cores in gates:
            if rect.collidepoint(px, py):
                if required and required in abilities:
                    continue
                if cores and "cores" in abilities:
                    continue
                return True
        tx, ty = int(px // TS), int(py // TS)
        if not tm.in_bounds(tx, ty):
            return True
        tile = tm.get(tx, ty)
        if tile == T_ONEWAY:
            return False
        if tile == T_CRYSTAL and "missile" in abilities:
            return False
        return tm.tileset[tile].solid

    def leg_clear(tm, x0, y0, x1, y1, abilities):
        steps = int(max(abs(x1 - x0), abs(y1 - y0)) / 5) + 1
        for i in range(steps + 1):
            t = i / steps
            x = x0 + (x1 - x0) * t
            y = y0 + (y1 - y0) * t
            for ox in (-6, 0, 6):
                for oy in (-9, 0, 9):
                    if blocked(x + ox, y + oy, tm, abilities):
                        return False
        return True

    return leg_clear


def analyse(abilities, verbose=False):
    level = build_level()
    tm = level.tilemap
    runs = surfaces(tm)
    leg_clear = make_blocker(level)
    double = "grav_boots" in abilities
    sx, sy = level.player_spawn
    start = min((r for r in runs if r["x0"] <= sx + 6 <= r["x1"] and r["y"] >= sy),
                key=lambda r: r["y"])
    seen = {id(start)}
    frontier = [start]
    while frontier:
        a = frontier.pop()
        for b in runs:
            if id(b) in seen:
                continue
            rise = a["y"] - b["y"]
            reach = double_jump_horizontal(rise) if double else jump_horizontal(rise)
            if reach is None:
                continue
            if b["x0"] > a["x1"]:
                gap = b["x0"] - a["x1"]
            elif a["x0"] > b["x1"]:
                gap = a["x0"] - b["x1"]
            else:
                gap = 0
            if gap > reach + 6:
                continue
            if b["x0"] >= a["x1"]:
                ax, bx = a["x1"] - 8, b["x0"] + 8
            elif a["x0"] >= b["x1"]:
                ax, bx = a["x0"] + 8, b["x1"] - 8
            else:
                ax = bx = min(max((a["x0"] + a["x1"]) / 2, b["x0"]), b["x1"])
            apex = min(a["y"], b["y"]) - 30
            if not (leg_clear(tm, ax, a["y"] - 11, ax, apex, abilities)
                    and leg_clear(tm, ax, apex, bx, apex, abilities)
                    and leg_clear(tm, bx, apex, bx, b["y"] - 11, abilities)):
                continue
            seen.add(id(b))
            frontier.append(b)

    unreachable = []
    for item, ix, iy in level.pickups:
        ok = any(id(r) in seen and r["x0"] - 60 <= ix <= r["x1"] + 60
                 and abs(r["y"] - iy) <= 120 for r in runs)
        if not ok:
            unreachable.append((item, int(ix // 24), int(iy // 24)))
    if verbose:
        print(f"abilities={sorted(abilities)} surfaces={len(seen)}/{len(runs)}")
        print(f"  unreachable: {unreachable or 'none'}")
    return unreachable


def main() -> int:
    from vesper.game.config import SURFACE_ONLY

    if SURFACE_ONLY:
        analyse(set(), verbose=True)
        print("SURFACE_ONLY is enabled — skipping underground gating checks")
        print("\nlevel validation OK (surface)")
        return 0

    steps = [
        ("start", set()),
        ("missile", {"missile"}),
        ("charge", {"missile", "charge"}),
        ("grav_boots", {"missile", "charge", "grav_boots"}),
    ]
    for label, abilities in steps:
        analyse(abilities, verbose=True)
        print(f"  -> {label}")

    # Key gating assertions.
    assert "missile" not in {i for i, _, _ in analyse(set())}, \
        "missile must be reachable from the start"
    assert "grav_boots" in {i for i, _, _ in analyse({"missile"})}, \
        "grav boots must be gated behind the charge beam"
    assert "grav_boots" not in {i for i, _, _ in analyse({"missile", "charge"})}, \
        "grav boots must be reachable once the charge beam is found"
    assert "dash" in {i for i, _, _ in analyse({"missile", "charge"})}, \
        "dash must be gated (needs grav boots)"
    assert not analyse({"missile", "charge", "grav_boots"}), \
        "all items must be reachable once grav boots are found"
    print("\nlevel validation OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
