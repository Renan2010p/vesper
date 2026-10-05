"""Procedural art: tiles."""

from __future__ import annotations

from ._base import *  # noqa: F401,F403
from ._base import _TS


def build_tile_surfaces(tileset, tile: int = _TS) -> Dict[int, pygame.Surface]:
    surfaces: Dict[int, pygame.Surface] = {}
    rng = random.Random(1337)
    for tile_id, definition in tileset.defs().items():
        if tile_id == 0:
            continue
        if definition.name == "surface_top":
            st = new_surface(tile, tile)
            st.fill(definition.color)
            speckle(st, definition.color2, count=9, rng=rng, size=2)
            # mossy / grassy top edge
            pygame.draw.rect(st, (52, 104, 74), (0, 0, tile, 3))
            pygame.draw.line(st, (86, 168, 116), (0, 0), (tile - 1, 0))
            for gx in range(1, tile, 4):
                pygame.draw.line(st, (74, 150, 104), (gx, 0), (gx, 4 + (gx % 3)))
            # a couple of pebbles
            pygame.draw.circle(st, definition.color2, (6, 12), 2)
            pygame.draw.circle(st, definition.color2, (17, 16), 1)
            surfaces[tile_id] = st
            continue
        s = new_surface(tile, tile)
        color = definition.color
        color2 = definition.color2
        s.fill(color)
        speckle(s, color2, count=10, rng=rng, size=2)
        # top highlight / bottom shade for solid blocks
        if definition.solid:
            pygame.draw.line(s, tuple(min(255, c + 26) for c in color), (0, 0), (tile - 1, 0))
            pygame.draw.line(s, tuple(max(0, c - 30) for c in color), (0, tile - 1), (tile - 1, tile - 1))
            pygame.draw.line(s, color2, (0, 2), (tile - 1, 2))
        if definition.oneway:
            s = new_surface(tile, 8)
            s.fill(color2)
            pygame.draw.line(s, color, (0, 0), (tile - 1, 0))
            pygame.draw.line(s, color, (0, 1), (tile - 1, 1))
        elif definition.hazard:
            s = new_surface(tile, tile)
            if definition.name in ("spike",):
                for i in range(3):
                    x = i * 8
                    pygame.draw.polygon(s, color, [(x, tile), (x + 4, 4), (x + 8, tile)])
                    pygame.draw.polygon(s, color2, [(x + 2, tile), (x + 4, 8), (x + 6, tile)])
            else:  # lava
                s.fill(color)
                for i in range(4):
                    yy = 4 + i * 5
                    pygame.draw.line(s, color2, (0, yy), (tile, yy), 1)
                speckle(s, (255, 240, 180), 6, rng)
        surfaces[tile_id] = s
    return surfaces
