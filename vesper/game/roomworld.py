"""Build one independent room (its own local tilemap and entities)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from vesper.engine.tilemap import TileMap

from .ascii_level import ITEM_BY_CHAR, TILE_BY_CHAR, parse
from .config import T_EMPTY, T_ROCK, TILE
from .rooms import ROOMS


@dataclass
class RoomData:
    id: str
    label: str
    zone: str
    tilemap: TileMap
    doors: List[dict] = field(default_factory=list)
    ship: Optional[Tuple[float, float]] = None
    spawn: Tuple[float, float] = (0.0, 0.0)
    saves: List[Tuple[float, float]] = field(default_factory=list)
    pickups: List[Tuple[str, float, float]] = field(default_factory=list)
    enemies: List[Tuple[str, float, float]] = field(default_factory=list)
    decorations: List[tuple] = field(default_factory=list)
    exits: Dict[str, dict] = field(default_factory=dict)


def _decorations_for(room_id: str, tm: TileMap, floor_row: int, width: int) -> List[tuple]:
    """The surface is kept clean; no scattered props for now."""
    return []


def build_room(room_id: str, tileset) -> RoomData:
    spec = ROOMS[room_id]
    amap = parse(spec["grid"], room_id)
    width, height = amap.width, amap.height
    tm = TileMap(width, height, TILE, tileset, fill=T_ROCK)

    ship = None
    spawn = None
    saves: List[Tuple[float, float]] = []
    pickups: List[Tuple[str, float, float]] = []
    for r, line in enumerate(amap.rows):
        for c, ch in enumerate(line):
            tile = TILE_BY_CHAR.get(ch)
            if tile is not None:
                tm.set(c, r, tile)

    # floor row = last row containing a wall
    floor_row = 0
    for r in range(height):
        if any(tm.get_def(c, r).solid and not tm.get_def(c, r).oneway
               for c in range(width)):
            floor_row = r

    # markers
    ship_override = spec.get("ship")
    if ship_override is not None:
        ship = (ship_override[0] * TILE, ship_override[1] * TILE)
    for _ch, c0, _r, length in amap.horizontal_runs("N"):
        if ship is None:
            ship = ((c0 + length // 2) * TILE, floor_row * TILE)
        break
    at = amap.first("@")
    if at is not None:
        spawn = (at[0] * TILE, at[1] * TILE)
    for _ch, c0, r0, _length in amap.horizontal_runs("S"):
        saves.append((c0 * TILE + TILE / 2, (r0 + 1) * TILE))
    for ch, c0, r0, _length in amap.horizontal_runs("".join(ITEM_BY_CHAR)):
        pickups.append((ITEM_BY_CHAR[ch], c0 * TILE + TILE / 2,
                        r0 * TILE + TILE / 2))

    # doors from exits (carve the opening at the edge, just above the floor)
    doors: List[dict] = []
    for side, link in spec.get("exits", {}).items():
        if side in ("left", "right"):
            ex = 0 if side == "left" else width - 1
            dy = link.get("at", floor_row - 2)
            for yy in (dy, dy + 1):
                tm.set(ex, yy, T_EMPTY)
            doors.append({"x": ex * TILE, "y": dy * TILE, "w": TILE, "h": 2 * TILE,
                          "tier": link.get("tier", 0), "axis": "v",
                          "target": link["to"], "enter": link.get("enter", side)})
        else:  # up / down
            ey = 0 if side == "up" else height - 1
            dx = link.get("at", width // 2)
            for xx in (dx, dx + 1):
                tm.set(xx, ey, T_EMPTY)
            doors.append({"x": dx * TILE, "y": ey * TILE, "w": 2 * TILE, "h": TILE,
                          "tier": link.get("tier", 0), "axis": "h",
                          "target": link["to"], "enter": link.get("enter", side)})

    if spawn is None:
        base_x = ship[0] if ship else (width // 2) * TILE
        spawn = (base_x - 4 * TILE, (floor_row - 2) * TILE)

    decorations = _decorations_for(room_id, tm, floor_row, width)
    enemies = [(name, tx * TILE + TILE / 2, ty * TILE + TILE / 2)
               for name, tx, ty in spec.get("enemies", [])]

    return RoomData(room_id, spec["label"], spec.get("zone", "surface"), tm,
                    doors=doors, ship=ship, spawn=spawn, saves=saves,
                    pickups=pickups, enemies=enemies, decorations=decorations,
                    exits=spec.get("exits", {}))


def build_room_graph() -> Dict[str, dict]:
    """Lay the rooms out on a little map, aligning connected doors.

    Returns ``{room_id: {"x","y","w","h","label","doors": {side: target}}}``
    in tile units.
    """
    from .rooms import ROOMS, START_ROOM

    info: Dict[str, dict] = {}
    for rid, spec in ROOMS.items():
        amap = parse(spec["grid"], rid)
        floor_row = 0
        for r in range(amap.height):
            if any(ch in "#!" for ch in amap.rows[r]):
                floor_row = r
        doors = {}
        for side, link in spec.get("exits", {}).items():
            if side in ("up", "down"):
                at = link.get("at", amap.width // 2)
            else:
                at = link.get("at", floor_row - 2)
            doors[side] = (link["to"], at)
        info[rid] = {"w": amap.width, "h": amap.height, "doors": doors,
                     "label": spec["label"]}

    opposite = {"left": "right", "right": "left", "up": "down", "down": "up"}
    graph: Dict[str, dict] = {START_ROOM: {"x": 0, "y": 0, **info[START_ROOM]}}
    queue = [START_ROOM]
    while queue:
        rid = queue.pop(0)
        a = graph[rid]
        for side, (to, at) in info[rid]["doors"].items():
            if to in graph:
                continue
            other = info[to]
            fallback = other["w"] // 2 if side in ("up", "down") else other["h"] - 3
            b_at = other["doors"].get(opposite[side], (None, fallback))[1]
            if side in ("left", "right"):
                bx = a["x"] + a["w"] if side == "right" else a["x"] - other["w"]
                by = a["y"] + at - b_at
            else:
                by = a["y"] + a["h"] if side == "down" else a["y"] - other["h"]
                bx = a["x"] + at - b_at
            graph[to] = {"x": bx, "y": by, **other}
            queue.append(to)
    return graph
