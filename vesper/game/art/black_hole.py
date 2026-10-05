"""Procedural art: black hole."""

from __future__ import annotations

from ._base import *  # noqa: F401,F403


_BH_CACHE: dict = {}


_BH_OVERLAY: dict = {}


def _black_hole_base(r: int) -> pygame.Surface:
    """Static parts (glow, disk, lensing) cached per radius."""
    cached = _BH_CACHE.get(r)
    if cached is not None:
        return cached
    size = int(r * 16)
    layer = pygame.Surface((size, size), pygame.SRCALPHA)
    c = size // 2

    # soft radial glow that fades fully to transparent (no square edge)
    steps = 70
    for k in range(steps, 0, -1):
        f = k / steps
        rr = r * (1.0 + f * 6.0)
        a = int(72 * (1 - f) ** 2.3)
        if a <= 0:
            continue
        pygame.draw.circle(layer, (255, 150, 85, a), (c, c), int(rr))

    # accretion disk: hot blue-white inner -> orange outer
    for k in range(40):
        f = k / 39
        rr = r * (1.12 + f * 2.3)
        a = int(175 * (1 - f) ** 0.85)
        col = (255, int(238 - 120 * f), int(228 - 170 * f))
        rect = (c - rr, c - rr * 0.26, rr * 2, rr * 0.52)
        pygame.draw.ellipse(layer, (*col, a), rect, 2)

    # Doppler beaming: the approaching side (right) is brighter
    for k in range(16):
        f = k / 15
        rr = r * (1.15 + f * 2.0)
        a = int(130 * (1 - f))
        rect = (c - rr, c - rr * 0.26, rr * 2, rr * 0.52)
        pygame.draw.arc(layer, (255, 250, 235, a), rect, -0.9, 0.9, 3)

    # gravitational lensing: the far side of the disk arcs over the top
    pygame.draw.arc(layer, (255, 226, 188, 180),
                    (c - r * 1.18, c - r * 1.22, r * 2.36, r * 1.3), 0.5, 2.64, 3)
    pygame.draw.arc(layer, (255, 210, 170, 130),
                    (c - r * 1.32, c - r * 1.46, r * 2.64, r * 1.6), 0.72, 2.42, 2)

    _BH_CACHE[r] = layer
    return layer


def draw_black_hole(surface, cx: int, cy: int, r: int, t: float) -> None:
    """Animated black hole: accretion disk, lensing and orbiting particles.

    Far-side particles are occluded by the event horizon; near-side ones pass in
    front of it.
    """
    base = _black_hole_base(r)
    c = base.get_width() // 2
    surface.blit(base, (cx - c, cy - c))

    size = int(r * 4)
    overlay = _BH_OVERLAY.get(r)
    if overlay is None:
        overlay = pygame.Surface((size, size), pygame.SRCALPHA)
        _BH_OVERLAY[r] = overlay
    overlay.fill((0, 0, 0, 0))
    cc = size // 2

    sparks = []
    for i in range(38):
        speed = 0.9 + (i % 4) * 0.3
        ang = t * speed + i * 0.19
        rr = r * (1.35 + (i % 6) * 0.26)
        trail = []
        for j in range(5):
            aa = ang - j * 0.05
            trail.append((cc + math.cos(aa) * rr, cc + math.sin(aa) * rr * 0.32))
        sparks.append((trail, math.sin(ang)))

    def draw_spark(trail):
        for j, (x, y) in enumerate(trail):
            a = int(235 * (1 - j / 5))
            col = (255, 240, 205, a) if j == 0 else (255, 180, 120, a)
            pygame.draw.circle(overlay, col, (int(x), int(y)), max(1, 3 - j))

    for trail, depth in sparks:
        if depth < 0:
            draw_spark(trail)

    # event horizon + photon ring
    pygame.draw.circle(overlay, (0, 0, 0, 255), (cc, cc), int(r))
    pygame.draw.circle(overlay, (215, 200, 255, 215), (cc, cc), int(r) + 1, 2)

    for trail, depth in sparks:
        if depth >= 0:
            draw_spark(trail)

    surface.blit(overlay, (cx - cc, cy - cc))
