#!/usr/bin/env python3
"""VESPER — Depths of Nara.

Bounty-hunter metroidvania.  Run with::

    python main.py

See README.md for controls and docs/ for architecture and modding guides.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Allow running directly from a checkout.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from vesper.engine.app import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main())
