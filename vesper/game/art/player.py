"""Procedural art: player."""

from __future__ import annotations

from ._base import *  # noqa: F401,F403
from ._base import _rect


def _hunter(aim: str = "side", leg: int = 0, bob: int = 0, arm: int = 0,
            gun_len: int = 3, hurt: bool = False, blink: bool = False) -> pygame.Surface:
    """Build one 18x24 frame of the heroine, facing right."""
    s = new_surface(18, 24)
    bob = bob
    body = SuitLight if hurt else Suit
    dark = SuitDark
    visor = VisorDim if blink else Visor
    # legs ---------------------------------------------------------------
    ly = 17 + bob
    if leg == 0:      # standing
        _rect(s, 6, ly, 3, 6, dark)
        _rect(s, 10, ly, 3, 6, body)
    elif leg == 1:    # run A
        _rect(s, 4, ly, 3, 5, dark)
        _rect(s, 11, ly, 3, 6, body)
    elif leg == 2:    # run B
        _rect(s, 6, ly, 3, 6, dark)
        _rect(s, 10, ly, 3, 5, body)
    elif leg == 3:    # run C
        _rect(s, 8, ly, 3, 5, body)
        _rect(s, 4, ly + 1, 3, 5, dark)
    elif leg == 4:    # tucked / jump
        _rect(s, 6, ly - 1, 4, 4, dark)
        _rect(s, 10, ly - 1, 3, 4, body)
    elif leg == 5:    # dash (stretched)
        _rect(s, 3, ly + 1, 4, 3, dark)
        _rect(s, 11, ly, 4, 3, body)
    elif leg == 6:    # hanging / wall
        _rect(s, 6, ly, 3, 4, dark)
        _rect(s, 9, ly + 1, 3, 5, body)
    elif leg == 7:    # run D (left forward)
        _rect(s, 5, ly, 3, 5, dark)
        _rect(s, 12, ly + 1, 3, 5, body)
    elif leg == 8:    # run E (right forward)
        _rect(s, 8, ly, 3, 6, dark)
        _rect(s, 4, ly + 1, 3, 5, body)
    elif leg == 9:    # landing squash
        _rect(s, 4, ly + 2, 4, 4, dark)
        _rect(s, 10, ly + 2, 4, 4, body)
    _rect(s, 6, ly + 5, 3, 2, Boot)
    _rect(s, 10, ly + 5, 3, 2, Boot)

    # ponytail -----------------------------------------------------------
    if leg == 5:  # trailing behind while dashing
        _rect(s, 1, 6 + bob, 5, 3, Hair)
        _rect(s, 2, 9 + bob, 3, 3, Hair)
    else:
        _rect(s, 3, 5 + bob, 3, 3, Hair)
        _rect(s, 2, 7 + bob, 3, 6, Hair)

    # torso --------------------------------------------------------------
    _rect(s, 6, 9 + bob, 7, 8, body)
    _rect(s, 7, 10 + bob, 5, 4, ArmorDark)
    _rect(s, 6, 15 + bob, 7, 2, dark)
    # shoulder -----------------------------------------------------------
    _rect(s, 11, 9 + bob, 3, 3, Armor)

    # head ---------------------------------------------------------------
    _rect(s, 6, 3 + bob, 7, 6, Armor)
    _rect(s, 6, 3 + bob, 7, 2, dark)
    _rect(s, 7, 6 + bob, 5, 2, ArmorDark)

    # arm + gun by aim ---------------------------------------------------
    ay = 11 + bob + arm
    if aim == "side":
        _rect(s, 12, ay, 4, 3, dark)
        _rect(s, 14, ay, gun_len, 3, Gun)
        _rect(s, 9, 5 + bob, 4, 3, visor)
    elif aim == "up":
        _rect(s, 9, 7 + bob, 3, 5, dark)
        _rect(s, 8, 1 + bob, 3, 9, Gun)
        _rect(s, 8, 4 + bob, 5, 3, visor)
    elif aim == "down":
        _rect(s, 11, ay + 2, 4, 4, dark)
        _rect(s, 12, ay + 5, 3, 5, Gun)
        _rect(s, 9, 5 + bob, 4, 3, visor)
    elif aim == "updiag":
        _rect(s, 11, ay - 1, 4, 3, dark)
        _rect(s, 13, ay - 4, 3, 5, Gun)
        _rect(s, 9, 4 + bob, 4, 3, visor)
    elif aim == "downdiag":
        _rect(s, 11, ay + 1, 4, 3, dark)
        _rect(s, 13, ay + 3, 3, 5, Gun)
        _rect(s, 9, 5 + bob, 4, 3, visor)
    return s


def player_animations() -> Dict[str, Animation]:
    anims: Dict[str, Animation] = {}
    for aim in ("side", "up", "down"):
        # idle: gentle breathing with an occasional visor blink
        idle = [_hunter(aim, leg=0, bob=b) for b in (0, 0, 0, 1, 1, 0, 0, 0)]
        idle[4] = _hunter(aim, leg=0, bob=1, blink=True)
        anims[f"idle_{aim}"] = Animation(idle, fps=7.0)
        # run: six-frame leg cycle with arm swing
        run = [
            _hunter(aim, leg=1, bob=-1, arm=1),
            _hunter(aim, leg=0, bob=0, arm=0),
            _hunter(aim, leg=3, bob=1, arm=-1),
            _hunter(aim, leg=2, bob=0, arm=0),
            _hunter(aim, leg=8, bob=-1, arm=1),
            _hunter(aim, leg=7, bob=0, arm=0),
        ]
        anims[f"run_{aim}"] = Animation(run, fps=14.0)
        anims[f"jump_{aim}"] = Animation([_hunter(aim, leg=4, bob=0)], fps=1.0)
        anims[f"fall_{aim}"] = Animation([_hunter(aim, leg=6, bob=0)], fps=1.0)
    anims["dash"] = Animation([_hunter("side", leg=5, bob=0, gun_len=4)], fps=1.0)
    anims["hurt"] = Animation([_hunter("side", leg=6, bob=0, hurt=True)], fps=1.0)
    anims["land"] = Animation([_hunter("side", leg=9, bob=2),
                               _hunter("side", leg=0, bob=0)], fps=12.0, loop=False)
    anims["skid"] = Animation([_hunter("side", leg=3, bob=1, arm=-1)], fps=1.0)

    # spin jump: the heroine somersaults in mid-air
    ball = new_surface(18, 24)
    pygame.draw.circle(ball, SuitDark, (9, 12), 8)
    pygame.draw.circle(ball, Suit, (9, 12), 7)
    pygame.draw.circle(ball, ArmorDark, (9, 12), 4)
    pygame.draw.circle(ball, Visor, (9, 12), 2)
    pygame.draw.line(ball, Armor, (9, 4), (9, 8), 2)          # marker to read rotation
    pygame.draw.circle(ball, Boot, (5, 16), 2)
    pygame.draw.circle(ball, Boot, (13, 16), 2)
    spin = []
    for i in range(8):
        rotated = pygame.transform.rotate(ball, -45 * i)
        canvas = new_surface(18, 24)
        canvas.blit(rotated, rotated.get_rect(center=(9, 12)).topleft)
        spin.append(canvas)
    anims["spin"] = Animation(spin, fps=18.0)
    return anims


def morph_animations() -> Dict[str, Animation]:
    frames = []
    for i in range(4):
        s = new_surface(16, 16)
        r = 7 - i
        pygame.draw.circle(s, SuitDark, (8, 8), 7)
        pygame.draw.circle(s, Suit, (8, 8), 6)
        pygame.draw.circle(s, ArmorDark, (8, 8), 4)
        # rolling visor band
        ang = i * math.pi / 2
        vx = int(8 + math.cos(ang) * 4)
        vy = int(8 + math.sin(ang) * 4)
        pygame.draw.circle(s, Visor, (vx, vy), 2)
        frames.append(s)
    return {"morph": Animation(frames, fps=14.0)}
