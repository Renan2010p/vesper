"""Todas as salas de Nara, escritas como grades de texto.

O jogo carrega UMA sala por vez.  Cada sala tem seu proprio tilemap local
(origem em 0,0) e e ligada as vizinhas por escotilhas nas bordas.  Ao
atravessar uma escotilha aberta, a sala de destino e carregada com fade.

Legenda
-------
``#`` parede      ``.`` / espaco = vazio     ``=`` plataforma
``^`` espinhos    ``~`` lava                 ``%`` parede quebravel   ``,`` musgo
``N`` nave        ``|`` escotilha            ``D`` escotilha          ``-`` escotilha
``@`` spawn       ``S`` ponto de save
``M C W G H K T X`` itens (missil, charge, forma, grav boots, dash, mag grip,
                    tanque de energia, tanque de missil)

Cada sala:
    label   chave i18n do nome mostrado ao entrar
    zone    zona de fundo ("surface" tem chuva)
    grid    a grade de texto
    exits   ligacoes: {"left"/"right": {"to": <sala>, "enter": "left"/"right",
                                         "tier": 0/1/2}}
"""

from __future__ import annotations

from typing import Dict


def _side(width: int, inner: str) -> str:
    """A row of ``width`` with walls on both sides and ``inner`` in between."""
    return "#" + inner.ljust(width - 2)[:width - 2] + "#"


LANDING_GRID = "\n".join([
    "########################",
    "#                      #",
    "#                      #",
    "#                      #",
    "#        NNNNN         #",
    "#                      #",
    "#                      #",
    "#                      #",
    "#                      #",
    "#        =====         #",
    "#                      #",
    "########################",
])

CAVE_GRID = "\n".join([
    "########################################",
    "#.....#......#.....#......#......#.....#",
    "#......................................#",
    "#......................................#",
    "#......................................#",
    "#......................................#",
    "#.............................##########",
    "#......................................#",
    "#......................................#",
    "#......................######..........#",
    "#......................................#",
    "#.................T....................#",
    "#...............######.................#",
    "#......................................#",
    "#......................................#",
    "#........######........................#",
    "#......................................#",
    "#......................................#",
    "#...######.............................#",
    "#......................................#",
    "#......................................#",
    "########################################",
])

CAVE2_GRID = "\n".join([
    _side(24, ""),                      # r0
    _side(24, ""),                      # r1
    _side(24, ""),                      # r2
    _side(24, " " * 11 + "====="),      # r3
    _side(24, ""),                      # r4
    _side(24, " " * 6 + "====="),       # r5
    _side(24, ""),                      # r6
    _side(24, " " * 2 + "====="),       # r7
    _side(24, ""),                      # r8
    _side(24, " " * 9 + "====="),       # r9
    _side(24, ""),                      # r10
    _side(24, ""),                      # r11
    _side(24, ""),                      # r12
    "#" * 24,                           # r13 floor
])

OUTER_GRID = "\n".join([
    _side(28, ""),
    _side(28, ""),
    _side(28, ""),
    _side(28, " " * 13 + "======"),
    _side(28, ""),
    _side(28, " " * 6 + "======"),
    _side(28, ""),
    _side(28, ""),
    _side(28, ""),
    _side(28, ""),
    _side(28, ""),
    "#" * 28,
])

ROOMS: Dict[str, Dict] = {
    "cave": {
        "label": "room.cave",
        "zone": "cave",
        "grid": CAVE_GRID,
        "exits": {
            "right": {"to": "landing", "enter": "left", "at": 4},
            "left": {"to": "cave2", "enter": "right"},
        },
        "enemies": [("crawler", 9, 19), ("flyer", 21, 7)],
    },
    "cave2": {
        "label": "room.cave2",
        "zone": "cave",
        "grid": CAVE2_GRID,
        "exits": {"right": {"to": "cave", "enter": "left"}},
        "enemies": [("crawler", 6, 11), ("crawler", 17, 11),
                    ("flyer", 19, 5), ("jumper", 11, 11)],
    },
    "landing": {
        "label": "zone.surface",
        "zone": "surface",
        "grid": LANDING_GRID,
        "exits": {
            "left": {"to": "cave", "enter": "right"},
            "right": {"to": "outer", "enter": "left"},
        },
    },
    "outer": {
        "label": "room.outer",
        "zone": "surface",
        "grid": OUTER_GRID,
        "exits": {"left": {"to": "landing", "enter": "right"}},
    },
}

#: the room the game starts in
START_ROOM = "landing"
