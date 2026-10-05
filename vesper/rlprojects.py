"""RL PROJECTS — studio identity and the Vesper development roadmap.

This module is the single source of truth for the studio branding and for the
three development stages that Vesper follows, mirroring how ``fnwf`` is built
on the Neko engine.  Import from here instead of hard-coding names.
"""

from __future__ import annotations

# -- studio -----------------------------------------------------------------
STUDIO = "RL PROJECTS"
COPYRIGHT = "Copyright (C) 2026 Renan Lucas Vieira Hilário"

#: engine that powers the current (Python) build
ENGINE = "Vesper engine"

# -- three-stage roadmap ----------------------------------------------------
#: The stage the code in this repository currently represents.
STAGE = 1

STAGES = {
    1: {
        "name": "Prototype",
        "tech": "Python + pygame",
        "goal": "Fast iteration on rules, level design and game feel.",
    },
    2: {
        "name": "Rewrite",
        "tech": "Zig + Neko engine",
        "goal": "Port the game to Neko so it is 100% Zig and shares the engine "
                "with the other RL PROJECTS games (fnwf).",
    },
    3: {
        "name": "Release",
        "tech": "all platforms",
        "goal": "Ship everywhere: Linux, Windows, macOS, web and PlayStation 2.",
    },
}


def stage_line() -> str:
    """Short human-readable description of the current stage."""
    info = STAGES[STAGE]
    return f"{info['tech']} · stage {STAGE}/{len(STAGES)}"
