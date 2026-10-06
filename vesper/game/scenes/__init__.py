"""Scene registry."""

from __future__ import annotations


def register_scenes(registry) -> None:
    from .cutscene import EscapeCutScene, FlyCutScene, StoryCutScene
    from .end import EndScene
    from .intro import IntroScene
    from .pause import PauseScene
    from .play import PlayScene
    from .saves import SaveSelectScene
    from .ship import ShipScene
    from .splash import SplashScene
    from .title import TitleScene

    registry.register("scene", "splash", SplashScene)
    registry.register("scene", "title", TitleScene)
    registry.register("scene", "intro", IntroScene)
    registry.register("scene", "play", PlayScene)
    registry.register("scene", "pause", PauseScene)
    registry.register("scene", "saves", SaveSelectScene)
    registry.register("scene", "ship", ShipScene)
    registry.register("scene", "end", EndScene)
    registry.register("scene", "cut_story", StoryCutScene)
    registry.register("scene", "cut_fly", FlyCutScene)
    registry.register("scene", "cut_escape", EscapeCutScene)
