"""Zeres Station — a small multi-room prologue area.

Rooms are plain grids (like the rest of the world) linked by doors.  The route
is: vertical elevator shaft (ship at the bottom) -> hall -> zig-zag corridor ->
two straight corridors -> the square boss chamber.  On the way back the player
must retrace the whole station before the self-destruct timer runs out.
"""

from __future__ import annotations

from typing import Dict, List


def _side(width: int, inner: str, ch: str = "!") -> str:
    return ch + inner.ljust(width - 2)[:width - 2] + ch


def _open(width: int, height: int, ch: str = "!") -> List[str]:
    return [ch * width] + [_side(width, "", ch) for _ in range(height - 2)] + [ch * width]


def _put(rows: List[str], row: int, col: int, text: str) -> None:
    r = rows[row]
    rows[row] = r[:col] + text + r[col + len(text):]


def _col(rows: List[str], col: int, r0: int, r1: int, ch: str = "!") -> None:
    for r in range(r0, r1 + 1):
        row = rows[r]
        rows[r] = row[:col] + ch + row[col + 1:]


# -- the elevator shaft (vertical; the gunship waits at the bottom) -----------
LIFT: List[str] = _open(12, 24)
for _r in (3, 6, 9, 12, 15, 18):
    _put(LIFT, _r, 1 if (_r // 3) % 2 else 7, "====")
_put(LIFT, 21, 4, "NNNN")     # gunship
_put(LIFT, 22, 2, "@")        # spawn

# -- a straight hall (links the shaft to the zig-zag) -------------------------
HALL: List[str] = _open(26, 10)

# -- the zig-zag corridor (pillars from floor and ceiling) --------------------
ZIGZAG: List[str] = _open(30, 12)
for _c in (8, 9, 24, 25):
    _col(ZIGZAG, _c, 1, 6)          # ceiling pillars
for _c in (16, 17):
    _col(ZIGZAG, _c, 7, 10)         # floor pillars (jump over)

# -- two straight runs --------------------------------------------------------
RUN: List[str] = _open(24, 10)
RUN2: List[str] = _open(24, 10)

# -- the square boss chamber --------------------------------------------------
BOSS: List[str] = _open(22, 18)

STATION_ROOMS: Dict[str, Dict] = {
    "station_lift": {
        "label": "zone.station", "zone": "station", "grid": LIFT,
        "exits": {"up": {"to": "station_hall", "enter": "down", "at": 8}},
    },
    "station_hall": {
        "label": "room.station_hall", "zone": "station", "grid": HALL,
        "exits": {
            "down": {"to": "station_lift", "enter": "up", "at": 5},
            "right": {"to": "station_zigzag", "enter": "left", "at": 7},
        },
    },
    "station_zigzag": {
        "label": "room.station_zigzag", "zone": "station", "grid": ZIGZAG,
        "exits": {
            "left": {"to": "station_hall", "enter": "right", "at": 9},
            "right": {"to": "station_run", "enter": "left", "at": 9},
        },
    },
    "station_run": {
        "label": "room.station_run", "zone": "station", "grid": RUN,
        "exits": {
            "left": {"to": "station_zigzag", "enter": "right", "at": 7},
            "right": {"to": "station_run2", "enter": "left", "at": 7},
        },
    },
    "station_run2": {
        "label": "room.station_run2", "zone": "station", "grid": RUN2,
        "exits": {
            "left": {"to": "station_run", "enter": "right", "at": 7},
            "right": {"to": "station_boss", "enter": "left", "at": 7},
        },
    },
    "station_boss": {
        "label": "room.station_boss", "zone": "station", "grid": BOSS,
        "exits": {"left": {"to": "station_run2", "enter": "right", "at": 15}},
        "enemies": [("zeres", 14, 8)],
    },
}
