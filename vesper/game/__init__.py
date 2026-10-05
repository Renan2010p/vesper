"""Vesper gameplay layer.

The package is intentionally split so content and rules live in different
places:

* ``components``  -> data only
* ``systems``     -> rules operating on that data
* ``prefabs`` / ``enemies`` / ``items`` / ``weapons`` -> content
* ``level``       -> level construction data
* ``scenes``      -> game states
* ``art``         -> procedural, original artwork

Adding an enemy, item or ability means registering content, not editing the
engine.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover
    from vesper.engine.app import App

START_SCENE = "splash"


def app_config():
    from vesper.engine.app import AppConfig
    from .config import FPS, LOGICAL_H, LOGICAL_W, TITLE

    return AppConfig(
        title=TITLE,
        window_size=(LOGICAL_W * 2, LOGICAL_H * 2),
        render_size=(LOGICAL_W, LOGICAL_H),
        fps=FPS,
        gravity=2200.0,
    )


def register_content(app: "App") -> None:
    """Register all built-in content (idempotent)."""
    from . import content, i18n

    # restore the saved language before building any text
    i18n.set_locale(app.get_setting("locale", i18n.DEFAULT_LOCALE))
    content.register_all(app)


def set_language(app: "App", locale: str) -> str:
    """Change language and persist the choice."""
    from . import i18n

    locale = i18n.set_locale(locale)
    app.set_setting("locale", locale)
    return locale
