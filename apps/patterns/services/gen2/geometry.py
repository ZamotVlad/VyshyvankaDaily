"""Силует сорочки 2.0: тулуб, рукави, манжети, відкладний комір і шия-манекен.

Ліва половина задана явно, права - дзеркальна відносно осі AXC.
Рукав має власну рамку: x упоперек (0 - зовнішній край, + до тулуба), y від плеча вниз.
"""

import math

W = 447.0
AXC = W / 2
VIEWBOX = f"-2 -4 {W + 4:g} 438"

# Рамка рукава
_ANGLE = math.radians(18)
N_ = (math.cos(_ANGLE), math.sin(_ANGLE))
D_ = (-math.sin(_ANGLE), math.cos(_ANGLE))
P0 = (103.0, 76.0)
SL_LEN = 325.0
SL_END_W = 60.0
CUFF_X, CUFF_W, CUFF_H = 5.0, 50.0, 22.0
SLEEVE_MATRIX = f"matrix({N_[0]:.4f} {N_[1]:.4f} {D_[0]:.4f} {D_[1]:.4f} {P0[0]:g} {P0[1]:g})"

Point = tuple[float, float]


def to_global(x: float, y: float) -> Point:
    return (P0[0] + x * N_[0] + y * D_[0], P0[1] + x * N_[1] + y * D_[1])


def to_frame(p: Point) -> Point:
    rx, ry = p[0] - P0[0], p[1] - P0[1]
    return (rx * N_[0] + ry * N_[1], rx * D_[0] + ry * D_[1])


def quad(p0: Point, p1: Point, p2: Point, n=8) -> list[Point]:
    return [
        (
            (1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t * t * p2[0],
            (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t * t * p2[1],
        )
        for t in (i / n for i in range(n + 1))
    ]


def mirror(p: Point) -> Point:
    return (W - p[0], p[1])


def poly(pts) -> str:
    return "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in pts) + "Z"


def polyline(pts) -> str:
    return "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in pts)


T_ = (126.0, 61.0)  # верх шва рукава
A_ = (125.5, 205.0)  # пахва
HEM_L = (123.5, 410.0)
NECK_L = (168.5, 42.2)
SEAM = quad(T_, (129, 135), A_, 12)
CAP = quad(T_, (113.5, 67.8), to_global(0, 16), 8)
SHOULDER = quad(NECK_L, (147, 51), T_, 8)
OC = to_global(0, SL_LEN)
IC = to_global(SL_END_W, SL_LEN)
# горловина під коміром
NECKLINE = [
    (
        AXC + 34 * math.cos(math.pi - (math.pi / 2) * i / 24),
        40 + 10 * math.sin(math.pi - (math.pi / 2) * i / 24),
    )
    for i in range(25)
]


def _edge_out(n=16) -> list[Point]:
    # зовнішній край з легкою опуклістю (тканина має об'єм)
    out = []
    for i in range(1, n + 1):
        y = 16 + (SL_LEN - 16) * i / n
        out.append(to_global(-6 * math.sin(math.pi * (y - 16) / (SL_LEN - 16)), y))
    return out


def _edge_in(n=16) -> list[Point]:
    a = to_frame(A_)
    out = []
    for i in range(n + 1):
        t = i / n
        y = SL_LEN + (a[1] - SL_LEN) * t
        out.append(to_global(SL_END_W + (a[0] - SL_END_W) * t + 5 * math.sin(math.pi * t), y))
    return out


EDGE_OUT = _edge_out()
EDGE_IN = _edge_in()
SLEEVE = CAP + EDGE_OUT + EDGE_IN[:-1] + SEAM[::-1][:-1]
CUFF = [
    to_global(CUFF_X, SL_LEN - 1),
    to_global(CUFF_X + CUFF_W, SL_LEN - 1),
    to_global(CUFF_X + CUFF_W - 1, SL_LEN + CUFF_H),
    to_global(CUFF_X + 1, SL_LEN + CUFF_H),
]


def _closed(left: list[Point]) -> list[Point]:
    hem = quad(HEM_L, (AXC, 414), mirror(HEM_L), 8)[1:-1]
    neck = [mirror(p) for p in NECKLINE] + NECKLINE[::-1]
    return left + hem + [mirror(p) for p in left[::-1]] + neck


BODY = _closed(SHOULDER + SEAM[1:] + [HEM_L])
OUTLINE = _closed(
    SHOULDER
    + CAP[1:]
    + EDGE_OUT[:-1]
    + [OC, CUFF[0], CUFF[3], CUFF[2], CUFF[1], IC]
    + EDGE_IN[1:]
    + [HEM_L]
)

_SLEEVE_F = [to_frame(p) for p in SLEEVE]


def sleeve_extent(y: float) -> tuple[float, float]:
    """Межі рукава по x на висоті y (рамка рукава)."""
    xs = []
    n = len(_SLEEVE_F)
    for i in range(n):
        (x1, y1), (x2, y2) = _SLEEVE_F[i], _SLEEVE_F[(i + 1) % n]
        if (y1 <= y < y2) or (y2 <= y < y1):
            xs.append(x1 + (y - y1) * (x2 - x1) / (y2 - y1))
    return (min(xs), max(xs)) if len(xs) >= 2 else (0.0, 0.0)


# ---------- комір і шия ----------
_K = 0.255


def _u(x, y) -> Point:
    """Координати еталонного макета коміра -> координати сорочки."""
    return (AXC + (x - 512) * _K, 61 + (y - 255) * _K)


NECK_X = AXC - 30.0
FLAP_TL, FLAP_TR, FLAP_TIP, FLAP_BL = (
    (168.5, 42.0),
    (NECK_X - 0.5, 24.0),
    _u(494, 249),
    (175.0, 81.0),
)
STAND = [FLAP_TL] + quad(FLAP_TL, (180, 31), FLAP_TR, 8)[1:] + [(NECK_X, 52), (176, 60), (166, 50)]
FLAP = (
    [FLAP_TL]
    + quad(FLAP_TL, (180, 31), FLAP_TR, 8)[1:]
    + quad(FLAP_TR, (NECK_X + 1, 45), (203, 52), 8)[1:]
    + [FLAP_TIP]
    + quad(FLAP_TIP, (196, 70), FLAP_BL, 8)[1:]
    + quad(FLAP_BL, (169.5, 62), FLAP_TL, 8)[1:-1]
)


def _inset(p: Point, q: Point, d: float) -> list[Point]:
    cx = sum(x for x, _ in FLAP) / len(FLAP)
    cy = sum(y for _, y in FLAP) / len(FLAP)
    dx, dy = q[0] - p[0], q[1] - p[1]
    length = math.hypot(dx, dy)
    nx, ny = -dy / length, dx / length
    if (cx - p[0]) * nx + (cy - p[1]) * ny < 0:
        nx, ny = -nx, -ny
    return [(p[0] + nx * d, p[1] + ny * d), (q[0] + nx * d, q[1] + ny * d)]


FLAP_BORDER_SIDE = _inset((168.9, 46), FLAP_BL, 4.4)
FLAP_BORDER_BOTTOM = _inset((FLAP_TIP[0] - 6, FLAP_TIP[1] + 2.6), FLAP_BL, 4.4)
NECK_TOP = 9.0
V_TIP = _u(512, 452)


def neck_path() -> str:
    """Шия заповнює простір між стійками коміра, нижче - вузький V до вузла."""
    left, right = NECK_X - 1, W - NECK_X + 1
    vx, vy = V_TIP
    return (
        f"M{left},{NECK_TOP} L{right},{NECK_TOP} L{right},48 C{right},56 {AXC + 11},55 {AXC + 8},60 "
        f"C{AXC + 6},72 {vx + 3:.1f},{vy - 14:.1f} {vx:.1f},{vy:.1f} "
        f"C{vx - 3:.1f},{vy - 14:.1f} {AXC - 6},72 {AXC - 8},60 C{AXC - 11},55 {left},56 {left},48 Z"
    )
