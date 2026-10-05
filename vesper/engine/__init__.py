"""Generic, game-agnostic engine layer.

Nothing in ``vesper.engine`` knows about Vesper's content (enemies, items,
levels...).  The game layer builds on top of these primitives.  This split is
what makes the project modular: the engine can be reused for other games and
the game can be extended without touching the engine.

Inside the engine there is a second split, mirroring the Neko engine:
``vesper.engine.platform`` is the only code that touches the OS (window,
events, keys, audio, fonts, files), and the rest of the engine is pure.  This
is what lets the game move from pygame (stage 1) to Zig/Neko (stage 2) without
being rewritten from scratch.  See ``docs/STAGES.md``.
"""
