"""Export the level as a plain-text grid drawn with '#'.

Usage::

    python -m tools.export_ascii_map [out.txt]

Legend: '#' wall, '=' ledge, '^' spike, '~' lava, '%' breakable, ',' deco.
"""

from __future__ import annotations

import sys

from vesper.game.hud import _tile_char
from vesper.game.level import build_level


def render() -> str:
    tm = build_level().tilemap
    return "\n".join(
        "".join(_tile_char(tm.get_def(tx, ty)) for tx in range(tm.width))
        for ty in range(tm.height)
    )


def main() -> int:
    out = sys.argv[1] if len(sys.argv) > 1 else "nara_map.txt"
    text = render()
    with open(out, "w", encoding="utf-8") as fh:
        fh.write(text + "\n")
    lines = text.splitlines()
    print(f"wrote {out} ({len(lines[0])}x{len(lines)})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
