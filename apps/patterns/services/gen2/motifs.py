"""Мотиви хрестиком. Власні, за мотивами регіональних типів (не копії музейних схем)."""

import math
from functools import cache

from .grid import Canvas, Pattern, from_rows

DIAG = ((-1, -1), (-1, 1), (1, -1), (1, 1))
AXES = ((-1, 0), (1, 0), (0, -1), (0, 1))


@cache
def star(radius=13) -> Pattern:
    """Восьмипелюсткова зірка."""
    n = 2 * radius + 3
    cv = Canvas(n, n)
    c = n // 2
    for dy, dx in AXES:
        cv.petal(c, c, dy, dx, 3, radius, 2, 0)
    for dy, dx in DIAG:
        cv.petal(c, c, dy, dx, 2, int(radius * 0.62), 1, 3)
    cv.rhomb(c, c, 3, 1)
    cv.rhomb(c, c, 1, 2)
    for dy, dx in DIAG:
        cv.rhomb(c + dy * int(radius * 0.62 + 3), c + dx * int(radius * 0.62 + 3), 1, 2)
    return cv.outline(1).pattern()


@cache
def rose(radius=5) -> Pattern:
    n = 4 * radius + 7
    cv = Canvas(n, n)
    c = n // 2
    for i in range(8):
        a = i * math.pi / 4
        cv.disk(
            c + math.sin(a) * (radius + 1.5),
            c + math.cos(a) * (radius + 1.5),
            radius * 0.45 + 0.6,
            0,
        )
    cv.disk(c, c, radius, 0)
    cv.disk(c, c, radius - 1.6, 2)
    cv.rhomb(c, c, 1, 1)
    for dy, dx in DIAG:
        cv.petal(c, c, dy, dx, radius + 3, radius + 6, 1, 4, over=False)
    return cv.outline(1).pattern()


@cache
def hook(radius=9) -> Pattern:
    """Ромб із «ріжками»."""
    n = 2 * radius + 9
    cv = Canvas(n, n)
    c = n // 2
    cv.rhomb(c, c, radius, 0, hollow=2)
    cv.rhomb(c, c, radius - 4, 2)
    cv.rhomb(c, c, radius - 6, 3)
    cv.rhomb(c, c, 0, 1)
    for dy, dx in AXES:
        br, bc = c + dy * (radius + 1), c + dx * (radius + 1)
        for s in (-1, 1):
            for a, b in ((0, 0), (1, 1), (2, 2), (2, 3), (1, 4), (0, 4)):
                cv.put(br + (dy * a if dy else s * b), bc + (dx * a if dx else s * b), 0)
    return cv.outline(1).pattern()


@cache
def rich(radius=9, inner="star") -> Pattern:
    """Великий ромб: темний обідок, світле кільце, зірка або ромб усередині, «ріжки» з боків."""
    n = 2 * radius + 5
    cv = Canvas(n, n)
    c = n // 2
    cv.rhomb(c, c, radius, 1, hollow=1)
    cv.rhomb(c, c, radius - 1, 0, hollow=2)
    cv.rhomb(c, c, radius - 3, 2, hollow=1)
    if inner == "star":
        for dy, dx in AXES:
            cv.petal(c, c, dy, dx, 1, radius - 5, 1, 0)
        for dy, dx in DIAG:
            cv.put(c + dy * 2, c + dx * 2, 3)
    else:
        cv.rhomb(c, c, radius - 6, 0, hollow=1)
        cv.rhomb(c, c, radius - 8 if radius > 9 else 1, 3)
    cv.put(c, c, 1)
    for s in (-1, 1):
        x = c + s * (radius + 1)
        for dy in (-2, -1, 0, 1, 2):
            cv.put(c + dy, x, 1 if abs(dy) == 2 else 0)
        cv.put(c - 2, x + s, 1)
        cv.put(c + 2, x + s, 1)
    return cv.pattern()


@cache
def tree(w=27, h=41, flower=True, pot=True) -> Pattern:
    """Дерево життя (з вазоном або без)."""
    cv = Canvas(w, h)
    c = w // 2
    top, bot = 7, h - (8 if pot else 2)
    cv.line(top, c, bot, c, 1)
    for i, y in enumerate(range(top + 5, bot - 2, 7)):
        length = 7 - i // 2
        for s in (-1, 1):
            cv.line(y, c, y - 3, c + s * length, 1)
            cv.petal(y - 1, c + s * 2, -1, s, 0, 4, 1, 4, over=False)
            cv.disk(y - 4, c + s * (length + 1), 1.4, 0)
            cv.put(y - 4, c + s * (length + 1), 2)
    if flower:
        cv.disk(top - 1, c, 3.2, 0)
        cv.disk(top - 1, c, 1.6, 2)
        cv.petal(top - 1, c, -1, -1, 2, 4, 1, 0)
        cv.petal(top - 1, c, -1, 1, 2, 4, 1, 0)
    if pot:
        for r in range(h - 7, h - 1):
            half = 6 - (r - (h - 7)) // 2
            for x in range(c - half, c + half + 1):
                cv.put(r, x, 0 if r != h - 5 else 2)
    return cv.outline(1).pattern()


@cache
def kalyna() -> Pattern:
    """Калина: листки з контуром, ягідки-хрестики на стеблинках."""
    cv = Canvas(25, 25)
    c = 12
    cv.petal(6, c, -1, -1, 0, 5, 2, 4)
    cv.petal(6, c, -1, 1, 0, 5, 2, 4)
    cv.outline(1)
    cv.line(4, c, 12, c, 1)
    for x in (c - 7, c, c + 7):
        cv.line(10, c, 13, x, 1)
    for y, x in ((16, c), (16, c - 7), (16, c + 7)):
        for dy, dx in ((0, 0), (3, -2), (3, 2), (6, 0), (0, -4), (0, 4)):
            for a, b in ((0, 0), (-1, 0), (1, 0), (0, -1), (0, 1)):
                cv.put(y + dy + a, x + dx + b, 0 if (a or b) else 2)
    return cv.pattern()


@cache
def grapes() -> Pattern:
    cv = Canvas(21, 29)
    c = 10
    cv.petal(5, c, -1, 0, 0, 4, 2, 4)
    cv.petal(5, c, 0, -1, 1, 7, 2, 4)
    cv.petal(5, c, 0, 1, 1, 7, 2, 4)
    cv.line(5, c, 10, c, 1)
    for i, k in enumerate((5, 5, 4, 4, 3, 2, 1)):
        for j in range(k):
            cv.disk(11 + i * 2.6, c + (j - (k - 1) / 2) * 2.7, 1.15, 2)
    return cv.outline(1).pattern()


@cache
def oak() -> Pattern:
    """Дубова гілка: лопаті листя й два жолуді."""
    cv = Canvas(21, 33)
    c = 10
    for i, y in enumerate(range(3, 21, 3)):
        length = (3, 4, 5, 5, 4, 3)[i]
        side = -1 if i % 2 == 0 else 1
        cv.petal(y, c, 0, side, 0, length, 1, 4)
        cv.petal(y + 1, c, 0, -side, 0, length - 1, 1, 4)
    cv.outline(1)
    cv.line(1, c, 26, c, 1)
    for x in (c - 4, c + 4):
        cv.line(23, c, 26, x, 1)
        cv.rhomb(27, x, 1, 1)
        cv.disk(29.5, x, 1.6, 0)
    return cv.pattern()


@cache
def sun(radius=10) -> Pattern:
    """Коло з розеткою (солярний знак)."""
    n = 2 * radius + 9
    cv = Canvas(n, n)
    c = n // 2
    for r in range(n):
        for x in range(n):
            if radius - 1.6 <= math.hypot(r - c, x - c) <= radius + 0.4:
                cv.put(r, x, 0)
    for i in range(16):
        a = i * math.pi / 8
        end = radius + (4 if i % 2 == 0 else 2)
        cv.line(
            c + math.sin(a) * (radius + 1.5),
            c + math.cos(a) * (radius + 1.5),
            c + math.sin(a) * end,
            c + math.cos(a) * end,
            0,
        )
    cv.rhomb(c, c, int(radius * 0.55), 2, hollow=1)
    cv.rhomb(c, c, int(radius * 0.3), 0)
    cv.rhomb(c, c, 0, 3)
    return cv.outline(1).pattern()


@cache
def sosonka(h=25) -> Pattern:
    cv = Canvas(17, h)
    c = 8
    cv.line(1, c, h - 2, c, 1)
    for i, y in enumerate(range(2, h - 3, 3)):
        length = min(2 + i, 7)
        for s in (-1, 1):
            cv.line(y, c, y + length * 0.7, c + s * length, 0)
    cv.put(0, c, 2)
    return cv.pattern()


@cache
def lily() -> Pattern:
    """Геометризована квітка у вазоні."""
    cv = Canvas(25, 37)
    c = 12
    cv.line(6, c, 30, c, 1)
    cv.line(18, c, 11, c - 7, 1)
    cv.line(18, c, 11, c + 7, 1)
    for y, x in ((5, c), (10, c - 7), (10, c + 7)):
        cv.petal(y, x, -1, 0, 0, 4, 2, 0)
        cv.petal(y, x, -1, -1, 0, 3, 1, 0)
        cv.petal(y, x, -1, 1, 0, 3, 1, 0)
        cv.put(y - 1, x, 2)
    cv.petal(24, c, -1, -1, 1, 6, 1, 4, over=False)
    cv.petal(24, c, -1, 1, 1, 6, 1, 4, over=False)
    for r in range(31, 37):
        half = 5 - (r - 31) // 2
        for x in range(c - half, c + half + 1):
            cv.put(r, x, 0 if r != 33 else 2)
    return cv.outline(1).pattern()


@cache
def periwinkle() -> Pattern:
    """Барвінок: п'ятипелюсткова квітка з листками."""
    cv = Canvas(19, 19)
    c = 9
    for i in range(5):
        a = -math.pi / 2 + i * 2 * math.pi / 5
        cv.disk(c + math.sin(a) * 3.6, c + math.cos(a) * 3.6, 2.1, 0)
    cv.disk(c, c, 1.2, 2)
    cv.petal(c, c, 1, -1, 5, 9, 1, 4, over=False)
    cv.petal(c, c, 1, 1, 5, 9, 1, 4, over=False)
    cv.outline(1)
    cv.put(c, c, 3)
    return cv.pattern()


@cache
def branch(h=31) -> Pattern:
    """Гілка: темне стебло, листки-ромби обабіч."""
    cv = Canvas(21, h)
    c = 10
    for r in range(h):
        cv.put(r, c + round(math.sin(r / 5) * 1.5), 1)
    for i, y in enumerate(range(2, h - 4, 5)):
        side = -1 if i % 2 else 1
        x = c + round(math.sin(y / 5) * 1.5)
        for t in range(1, 8):
            w = 1 if 2 <= t <= 5 else 0
            for j in range(-w, w + 1):
                cv.put(y - t // 2 + j, x + side * t, 0)
    cv.rhomb(0, c, 1, 0)
    return cv.pattern()


BIRD_ROWS = [
    "......##.......",
    ".....#oo#......",
    "....#o#oo##....",
    "....#oooo#2#...",
    "...#ooooo##....",
    "#.#oooooo#.....",
    "##ooooooo#.....",
    "#o3o3ooo#......",
    ".#ooooo#.......",
    "..##o##........",
    "....#.#........",
    "...##.##.......",
]


@cache
def bird() -> Pattern:
    return from_rows(BIRD_ROWS, {"#": 1, "o": 0, "2": 2, "3": 3})


@cache
def birds_tree() -> Pattern:
    """Два птахи біля дерева життя."""
    cv = Canvas(45, 27)
    cv.stamp(tree(15, 27, flower=True, pot=False), 0, 15)
    cv.stamp(bird(), 12, 0, mirror=True)
    cv.stamp(bird(), 12, 30)
    return cv.pattern()


@cache
def kalyna_birds() -> Pattern:
    """Калина між двома пташками."""
    cv = Canvas(33, 28)
    c = 16
    cv.line(0, c, 9, c, 1)
    for x in (c - 6, c, c + 6):
        cv.line(4, c, 7, x, 1)
    for y, x in ((10, c), (10, c - 6), (10, c + 6)):
        for dy, dx in ((0, 0), (2, -2), (2, 2), (4, 0), (0, -3), (0, 3)):
            for a, b in ((0, 0), (-1, 0), (1, 0), (0, -1), (0, 1)):
                cv.put(y + dy + a, x + dx + b, 0 if (a or b) else 2)
    cv.leaf(3, c, -1, -1.4, 5, 1.6)
    cv.leaf(3, c, -1, 1.4, 5, 1.6)
    cv.stamp(bird(), 16, 1, mirror=True)
    cv.stamp(bird(), 16, 17)
    return cv.pattern()


ORLYK_ROWS = [
    "...oo.........oo...",
    "..o2oo.......oo2o..",
    "...ooo.......ooo...",
    "....oo.......oo....",
    ".....oo..o..oo.....",
    "o.....ooooooo.....o",
    "oo....oo222oo....oo",
    "ooo..oo22222oo..ooo",
    ".ooo.o222+222o.ooo.",
    "..oooo222+222oooo..",
    "...ooo2222222ooo...",
    "....oo2222222oo....",
    "......oo222oo......",
    ".......o222o.......",
    "......oo.o.oo......",
    ".....oo..o..oo.....",
    "....oo...o...oo....",
    ".........o.........",
]


@cache
def orlyk() -> Pattern:
    """Стилізований двоголовий орел («орлик»)."""
    p = from_rows(ORLYK_ROWS, {"o": 0, "2": 2, "+": 3})
    cv = Canvas(p.w + 2, p.h + 2)
    cv.stamp(p, 1, 1)
    return cv.outline(1).pattern()


@cache
def curl() -> Pattern:
    cv = Canvas(7, 7)
    for r, c in (
        (0, 2), (0, 3), (0, 4), (1, 5), (2, 6), (3, 6), (4, 5),
        (4, 4), (3, 3), (2, 3), (5, 1), (6, 0), (4, 2),
    ):  # fmt: skip
        cv.put(r, c, 0)
    return cv.pattern()


@cache
def cross() -> Pattern:
    cv = Canvas(15, 15)
    c = 7
    for dy, dx in AXES:
        cv.petal(c, c, dy, dx, 1, 6, 1, 0)
        cv.rhomb(c + dy * 6, c + dx * 6, 1, 2)
    cv.rhomb(c, c, 1, 3)
    return cv.outline(1).pattern()


@cache
def small_star() -> Pattern:
    cv = Canvas(11, 11)
    c = 5
    for dy, dx in AXES:
        cv.petal(c, c, dy, dx, 1, 4, 1, 0)
    for dy, dx in DIAG:
        cv.petal(c, c, dy, dx, 1, 2, 0, 3)
    cv.put(c, c, 2)
    return cv.pattern()


@cache
def small_rhomb() -> Pattern:
    cv = Canvas(9, 9)
    cv.rhomb(4, 4, 4, 0, hollow=1)
    cv.rhomb(4, 4, 2, 2)
    cv.put(4, 4, 1)
    return cv.pattern()


@cache
def crown() -> Pattern:
    cv = Canvas(17, 13)
    for x in (2, 8, 14):
        cv.line(1, x, 8, x, 0)
        cv.rhomb(1, x, 1, 2)
    cv.line(8, 2, 8, 14, 0)
    cv.line(10, 1, 10, 15, 0)
    for x in range(2, 15, 2):
        cv.put(9, x, 3)
    cv.line(5, 2, 8, 5, 0)
    cv.line(5, 14, 8, 11, 0)
    return cv.outline(1).pattern()


# ---------- троянди в стилі буковинської гладі-хрестика ----------
# Ролі: 0 червоний, 1 стебло, 3 листя, 4 жилка, 5 темно-червоний, 6 світло-червоний


def _rose_head(cv: Canvas, cy, cx, r=4.8):
    """Троянда: спіраль пелюсток темно-червоним, світліший край."""
    for y in range(int(cy - r - 1), int(cy + r + 2)):
        for x in range(int(cx - r - 1), int(cx + r + 2)):
            dy, dx = y - cy, x - cx
            d = math.hypot(dy, dx)
            if d > r + 0.35:
                continue
            a = math.atan2(dy, dx)
            t = (a + math.pi) / (2 * math.pi)
            k = 0
            if d < 1.0 or abs(d - (1.6 + 2.2 * t)) < 0.55:
                k = 5
            elif d > r - 1.1 and math.sin(a - 0.7) > 0.35:
                k = 5
            elif d > r - 1.4 and math.sin(a + 2.4) > 0.55:
                k = 6
            cv.put(y, x, k)


def _bud(cv: Canvas, cy, cx):
    for dy, dx in ((0, 0), (-1, 0), (1, 0), (0, -1), (0, 1), (-2, 0)):
        cv.put(cy + dy, cx + dx, 0 if (dy, dx) != (0, 0) else 5)
    cv.put(cy + 2, cx - 1, 3)
    cv.put(cy + 2, cx + 1, 3)
    cv.put(cy + 2, cx, 4)


@cache
def rose_vine(w=24, period=26, reps=10) -> Pattern:
    """Пари троянд обабіч стебла, пари листків, пуп'янки."""
    cv = Canvas(w, period * reps)
    c = w // 2
    for rep in range(reps):
        y0 = rep * period
        for t in range(period):
            cv.put(y0 + t, c + round(0.8 * math.sin(2 * math.pi * t / period)), 1)
        _rose_head(cv, y0 + 6, c - 5.5)
        _rose_head(cv, y0 + 6, c + 5.5)
        cv.leaf(y0 + 14, c, 1, -1.3, 7, 2)
        cv.leaf(y0 + 14, c, 1, 1.3, 7, 2)
        side = -1 if rep % 2 else 1
        _bud(cv, y0 + 22, c + 4 * side)
        cv.line(y0 + 24, c, y0 + 23, c + 3 * side, 1)
    return cv.pattern()


@cache
def rose_branch() -> Pattern:
    """Гілка з двома трояндами для кінця коміра."""
    cv = Canvas(26, 30)
    for t in range(2, 29):
        cv.put(t, 9 + round(t * 0.25 + 1.5 * math.sin(t / 4)), 1)
    cv.leaf(11, 11, -0.6, -1, 7, 2)
    cv.leaf(22, 15, 0.3, 1, 6, 2)
    cv.leaf(5, 10, -1, 1, 5, 1.5)
    _rose_head(cv, 7, 13, 4.2)
    _rose_head(cv, 18, 13, 5.0)
    _bud(cv, 27, 9)
    return cv.pattern()
