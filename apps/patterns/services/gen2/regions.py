"""Рецепти вишиванок 27 регіонів.

Кожен рецепт розкладає мотиви по зонах (пазуха, уставка, поли рукава, манжети, кінці коміра).
Варіанти (мотив пазухи, компонування рукава, колір шнурків) обираються rng дати,
тож та сама дата завжди дає ту саму сорочку. На кінцях коміра - мотив регіону з бази
(«Мотиви» на сторінці дня), щоб текст і малюнок збігались.
Палітри - з Region.dominant_colors/accent_colors і паспортів Музею Івана Гончара (DMC).
"""

import random
from collections.abc import Callable

from . import motifs as M
from . import regional as R
from .grid import (
    Pattern,
    b_chain,
    b_dots,
    b_kryv,
    b_line,
    b_meander,
    b_repeat,
    b_teeth,
    b_wave,
    column,
    stack,
)
from .shirt import SLEEVE_END as END
from .shirt import Shirt

BL, CH = "#1d1916", "#6b1521"
Recipe = Callable[[Shirt, random.Random], None]


def _cells(fn, w=0) -> Pattern:
    return Pattern(fn, w)


def _band(
    motif: Pattern, edge: int, teeth_role: int = 0, flip_role: int | None = None, gap=2
) -> Pattern:
    """Уставка: лінія, зубці, мотиви в ряд, зубці, лінія."""
    fr = teeth_role if flip_role is None else flip_role
    return stack(
        (1, b_line(edge)),
        (3, b_teeth(3, teeth_role)),
        (1, None),
        (motif.h, b_repeat(motif, gap)),
        (1, None),
        (3, b_teeth(3, fr, flip=True)),
        (1, b_line(edge)),
    )


def _kryv_flap(roles=(0, 2, 3)) -> Pattern:
    def cell(r, c):
        band = r // 5
        if r % 5 == round(abs((c % 6) - 3) * 4 / 3):
            return roles[band % len(roles)]
        return None

    return Pattern(cell, 24, 24)


def _tiled(m: Pattern, nx=2, ny=2, gap=1) -> Pattern:
    w, h = m.w * nx + gap * (nx - 1), m.h * ny + gap * (ny - 1)

    def cell(r, c):
        y, x = r % (m.h + gap), c % (m.w + gap)
        return m(y, x) if y < m.h and x < m.w else None

    return Pattern(cell, w, h)


# ======================================================================


def vinnytska(sh: Shirt, rng: random.Random):
    us = stack(
        (1, b_dots(0)), (2, b_teeth(2, 0)), (1, None), (17, R.nyz), (1, None),
        (2, b_teeth(2, 0, flip=True)), (1, b_dots(0)),
    )  # fmt: skip
    y = sh.ustavka(us, 66, 1.44, "satin")

    sh.stripes(R.curly_vine, 13, (-0.5, 0.5), y + 8, END, 1.36)
    big = rng.choice([M.rich(10, "rhomb"), M.rich(10, "star")]).recolor({0: 0, 2: 3, 3: 2})
    strip = (
        lambda r, c: 0 if abs(r % 6 - 3) == abs(c - 2) or (c in (0, 4) and r % 2 == 0) else None,
        5,
        286,
    )
    sh.pazukha(column(big, side=0), big.w + 4, 68, 280, 1.44, 34, tech="satin", strip=strip)
    sh.cuffs(
        stack(
            (1, b_line(0)), (1, None), (7, lambda r, c: R.nyz(r + 6, c)), (1, None), (1, b_line(0))
        ),
        1.52,
        "satin",
    )
    sh.flap_fill = M.rich(8, "rhomb").recolor({2: 3, 3: 2})


def volynska(sh: Shirt, rng: random.Random):
    st = M.star(10)
    y = sh.ustavka(_band(st, 1, 2), 60, 1.28)
    for yy in (y + 30, y + 80, y + 130):
        if yy + 14 < END:
            sh.ustavka(stack((1, b_line(1)), (5, b_chain(0, 2)), (1, b_line(1))), yy, 1.36)
    main = rng.choice([st, M.hook(9).recolor({2: 2, 3: 3})])
    strip = (lambda r, c: 2 if abs(r % 6 - 3) + abs(c - 2) == 2 else None, 5, 286)
    sh.pazukha(column(main, gap=1, side="dots"), main.w + 4, 68, 280, 1.36, 38, strip=strip)
    sh.cuffs(
        stack(
            (3, b_teeth(3, 0)),
            (1, None),
            (5, b_chain(2, 0)),
            (1, None),
            (3, b_teeth(3, 0, flip=True)),
        ),
        1.28,
    )
    sh.flap_fill = M.star(9)


def dnipropetrovska(sh: Shirt, rng: random.Random):
    lily = M.lily().recolor({4: 2})
    us = stack(
        (1, b_line(1)),
        (4, b_wave(0, 4, 8)),
        (1, None),
        (lily.h, b_repeat(lily, 1)),
        (1, None),
        (1, b_line(1)),
    )
    y = sh.ustavka(us, 52, 1.2)
    sh.scatter(M.small_star().recolor({3: 2}), y + 14, END, 1.44, 30, n=2)
    main = rng.choice([lily, M.sun(10)])
    sh.pazukha(column(main, gap=2, side=1), main.w + 4, 68, 286, 1.28, 34)
    sh.cuffs(
        stack((1, b_line(1)), (4, b_wave(0, 4, 8)), (1, None), (5, b_chain(2, 0)), (1, b_line(1))),
        1.44,
    )
    sh.flap_fill = M.sun(8)


def donetska(sh: Shirt, rng: random.Random):
    rose = M.rose(4)
    y = sh.ustavka(_band(rose, 1, 0, gap=2), 64, 1.36)
    sh.scatter(rose, y + 18, END, 1.36, 44, n=2)
    main = rng.choice([M.tree(31, 49), M.lily().recolor({4: 4})])
    sh.pazukha(column(main, gap=3, side="dots"), main.w + 4, 68, 286, 1.24, 34)
    sh.cuffs(
        stack((1, b_line(1)), (1, None), (rose.h, b_repeat(rose, 2)), (1, None), (1, b_line(1))),
        1.04,
    )
    sh.flap_fill = M.rose(5)


def zhytomyrska(sh: Shirt, rng: random.Random):
    hk = M.hook(9)
    y = sh.ustavka(_band(hk, 1, 0, gap=1), 60, 1.28)
    bv = M.periwinkle().recolor({0: 2, 3: 3})
    sh.column(bv, -0.35, y + 12, END, 1.44, gap=18)
    sh.column(bv, 0.45, y + 44, END, 1.44, gap=18)
    main = rng.choice([hk, M.star(9)])
    sh.pazukha(column(main, side=1), main.w + 4, 68, 286, 1.36, 34)
    sh.cuffs(
        stack(
            (3, b_teeth(3, 0)),
            (1, None),
            (5, b_chain(2, 0)),
            (1, None),
            (3, b_teeth(3, 0, flip=True)),
        ),
        1.28,
    )
    sh.hem(stack((1, b_line(1)), (hk.h, b_repeat(hk, 2)), (1, b_line(1))), 1.28)
    sh.flap_fill = M.star(8)


def zakarpatska(sh: Shirt, rng: random.Random):
    us = stack(
        (1, b_line(1)), (4, b_kryv(4, 0, 6)), (1, b_dots(2)), (5, b_chain(3, 2)), (1, b_dots(2)),
        (4, b_kryv(4, 4, 6)), (1, b_line(1)), (3, b_teeth(3, 0)), (3, b_teeth(3, 1, flip=True)),
        (1, b_line(2)), (5, b_chain(0, 3)), (1, b_line(1)),
    )  # fmt: skip
    y = sh.ustavka(us, 60, 1.28)

    def stripe(r, c):
        if r % 6 == round(abs(c - 3) * 5 / 3):
            return (0, 2, 3, 4)[r // 6 % 4]
        return 1 if c in (0, 6) else None

    sh.stripes(stripe, 7, (0,), y + 10, END, 1.28)
    order = rng.choice([(0, 1, 2, 3, 0, 4), (0, 2, 4, 3, 1, 2)])

    def zig(r, c):
        if c in (0, 21):
            return 1
        if r % 5 == round(abs(c % 6 - 3) * 4 / 3):
            return order[r // 5 % 6]
        return None

    sh.pazukha(_cells(zig, 22), 22, 68, 286, 1.36, 34)
    sh.cuffs(
        stack(
            (1, b_line(1)),
            (4, b_kryv(4, 0, 6)),
            (1, b_dots(2)),
            (4, b_kryv(4, 3, 6)),
            (1, b_line(1)),
        ),
        1.36,
    )
    sh.flap_fill = _kryv_flap((0, 2, 3, 4))


def zaporizka(sh: Shirt, rng: random.Random):
    sun = M.sun(10)
    us = stack(
        (1, b_line(1)),
        (1, None),
        (sun.h, b_repeat(sun, 1)),
        (1, None),
        (1, b_line(1)),
        (5, b_chain(0, 2)),
        (1, b_line(1)),
    )
    y = sh.ustavka(us, 56, 1.12)
    sh.column(M.kalyna(), 0, y + 16, END, 1.36, gap=20)
    main = rng.choice([sun, M.kalyna()])
    sh.pazukha(column(main, gap=2, side="dots"), main.w + 4, 68, 286, 1.2, 34)
    sh.cuffs(
        stack((1, b_line(1)), (7, b_repeat(M.small_star().recolor({3: 2}), 2)), (1, b_line(1))),
        1.44,
    )
    sh.flap_fill = M.sun(8)


def ivano_frankivska(sh: Shirt, rng: random.Random):
    roles = rng.choice([(3, 0, 2), (0, 3, 2)])
    y = sh.knot_rows(62, 14, 3.2, roles) + 3
    sh.ustavka(stack((1, b_line(1)), (5, b_chain(0, 2)), (1, b_line(1))), y, 1.36)
    rh = M.small_rhomb()
    sh.stripes(
        lambda r, c: 1 if c in (0, 10) else (rh(r % 9, c - 1) if 1 <= c <= 9 else None),
        11,
        (-0.45, 0.5),
        y + 18,
        END,
        1.36,
    )

    sh.pazukha(_cells(R.chevron, 20), 20, 68, 286, 1.44, 34)
    for side in (-1, 1):
        for i in range(5):
            sh.knot(223.5 + side * (60 + i * 5), 74 + i * 9, 3.2, roles[i % 3])
    sh.cuffs(
        stack((1, b_line(1)), (2, b_line(3)), (5, b_chain(0, 2)), (2, b_line(3)), (1, b_line(1))),
        1.36,
    )
    sh.flap_fill = M.hook(8)


def kyivska(sh: Shirt, rng: random.Random):
    br = M.branch(39)
    y = sh.ustavka(_band(br, 1, 0, gap=0), 58, 1.2)
    sh.column(br, -0.48, y + 10, END, 1.16, gap=4)
    sh.column(br, 0.52, y + 34, END, 1.16, gap=4)
    main = rng.choice([br, M.grapes().recolor({2: 0, 4: 1})])
    sh.pazukha(column(main, side="dots", k=1), main.w + 4, 68, 286, 1.36, 34)

    def cuff(r, c):
        return 0 if abs(r - 2) + abs(c % 7 - 3) <= 1 else (1 if r == 2 else None)

    sh.cuffs(stack((1, b_line(1)), (2, None), (5, cuff), (2, None), (1, b_line(1))), 1.44)
    sh.flap_fill = M.grapes().recolor({2: 0, 4: 1})


def kirovohradska(sh: Shirt, rng: random.Random):
    rose = M.rose(5)
    y = sh.ustavka(_band(rose, 1, 4, gap=2), 60, 1.2)
    sh.column(M.tree(29, 47), 0, y + 12, END, 1.2, gap=10)
    main = rng.choice([M.tree(31, 49), M.lily().recolor({4: 4})])
    sh.pazukha(column(main, gap=2, side=1), main.w + 4, 68, 286, 1.24, 34)
    sh.cuffs(stack((1, b_line(1)), (rose.h, b_repeat(rose, 2)), (1, b_line(1))), 0.84)
    sh.flap_fill = M.tree(19, 29)


def luhanska(sh: Shirt, rng: random.Random):
    y = sh.ustavka(
        stack((1, b_line(1)), (1, None), (22, R.squares), (1, None), (1, b_line(1))), 60, 1.28
    )
    sh.scatter(M.small_star().recolor({3: 2}), y + 14, END, 1.44, 28, n=2)
    if rng.random() < 0.5:
        sh.pazukha(_cells(R.squares, 22), 22, 68, 286, 1.44, 34)
    else:
        lily = M.lily().recolor({4: 2})
        sh.pazukha(column(lily, gap=2, side=1), lily.w + 4, 68, 286, 1.28, 34)
    sh.cuffs(stack((11, R.squares)), 1.52)
    sh.flap_fill = M.lily().recolor({4: 2})


def lvivska(sh: Shirt, rng: random.Random):
    sos = M.sosonka(24).recolor({0: 2})
    y = sh.ustavka(
        stack((1, b_dots(1)), (1, None), (sos.h, b_repeat(sos, 2)), (1, None), (1, b_dots(1))),
        62,
        1.28,
    )
    for yy, k in ((y + 34, 4), (y + 96, 3), (y + 158, 2)):
        if yy + 12 < END:
            sh.ustavka(
                stack(
                    (1, b_line(1)),
                    (3, b_teeth(3, k)),
                    (3, b_teeth(3, 1, flip=True)),
                    (1, b_line(1)),
                ),
                yy,
                1.28,
            )
    main = rng.choice([sos, M.sosonka(24).recolor({0: 4})])
    sh.pazukha(column(main, gap=2, side="dots"), main.w + 4, 68, 286, 1.36, 34)
    sh.cuffs(
        stack((1, b_line(1)), (4, b_teeth(4, 2)), (4, b_teeth(4, 4, flip=True)), (1, b_line(1))),
        1.36,
    )
    sh.flap_fill = M.sosonka(21).recolor({0: 2})


def mykolaivska(sh: Shirt, rng: random.Random):
    oak = M.oak()
    us = stack(
        (1, b_line(1)),
        (4, b_wave(2, 4, 10)),
        (1, None),
        (oak.h, b_repeat(oak, 1)),
        (1, None),
        (4, b_wave(2, 4, 10)),
        (1, b_line(1)),
    )
    y = sh.ustavka(us, 54, 1.12)
    sh.column(oak, -0.45, y + 10, END, 1.12, gap=12)
    sh.column(oak, 0.5, y + 40, END, 1.12, gap=12)
    main = rng.choice([oak, M.sosonka(24)])
    sh.pazukha(column(main, gap=2, side=2), main.w + 4, 68, 286, 1.28, 34)
    sh.cuffs(
        stack(
            (1, b_line(1)), (4, b_wave(0, 4, 10)), (1, None), (4, b_wave(2, 4, 10)), (1, b_line(1))
        ),
        1.44,
    )
    sh.flap_fill = M.sosonka(21)


def odeska(sh: Shirt, rng: random.Random):
    cr = M.crown()
    us = stack(
        (1, b_line(1)),
        (cr.h, b_repeat(cr, 2)),
        (1, None),
        (1, b_line(2)),
        (15, b_repeat(M.cross(), 2)),
        (1, b_line(1)),
    )
    y = sh.ustavka(us, 58, 1.16)
    sh.scatter(M.cross(), y + 16, END, 1.2, 44, n=2)
    main = rng.choice([M.cross(), M.orlyk().recolor({0: 1, 1: 1, 2: 2, 3: 0})])
    sh.pazukha(column(main, gap=1, side=2), main.w + 4, 68, 286, 1.52 if main.w < 18 else 1.28, 34)
    sh.cuffs(stack((1, b_line(2)), (cr.h, b_repeat(cr, 2)), (1, b_line(2))), 1.12)
    sh.flap_fill = M.orlyk().recolor({0: 1, 1: 1, 2: 2, 3: 0})


def poltavska(sh: Shirt, rng: random.Random):
    st = M.star(9).recolor({1: 3, 2: 1, 3: 0})
    us = stack(
        (1, b_dots(1)),
        (3, b_teeth(3, 0)),
        (1, None),
        (st.h, b_repeat(st, 2)),
        (1, None),
        (3, b_teeth(3, 0, flip=True)),
        (1, b_dots(1)),
    )
    y = sh.ustavka(us, 58, 1.28)
    for x in (16, 40):
        sh.gilce("sleeve", x, y + 8, END - y - 8, 0.8)
    main = rng.choice([st, M.rich(10, "rhomb").recolor({1: 3, 2: 1, 3: 2})])
    sh.pazukha(column(main, gap=2, side="dots", k=3), main.w + 4, 68, 286, 1.36, 34)
    sh.cuffs(
        stack((1, b_dots(1)), (3, b_teeth(3, 0)), (3, b_teeth(3, 0, flip=True)), (1, b_dots(1))),
        1.52,
    )
    sh.hem(stack((1, b_dots(1)), (st.h, b_repeat(st, 3)), (1, b_dots(1))), 1.12)
    sh.flap_fill = M.branch(31).recolor({0: 0, 1: 3})


def rivnenska(sh: Shirt, rng: random.Random):
    hk = M.hook(9).recolor({1: 0, 2: 2, 3: 0})
    sh.ustavka(_band(hk, 0, 0, gap=2), 60, 1.28)

    sh.ustavka(stack((1, b_line(0)), (20, R.zavolikannia), (1, b_line(0))), END - 44, 1.44, "satin")
    main = rng.choice([M.rich(11, "star"), M.rich(11, "rhomb")]).recolor({1: 0, 2: 0, 3: 2})
    sh.pazukha(column(main, side=0), main.w + 4, 68, 286, 1.28, 34)
    sh.cuffs(stack((1, b_line(0)), (8, R.zavolikannia), (1, b_line(0))), 1.52, "satin")
    sh.hem(stack((1, b_line(0)), (14, R.zavolikannia), (1, b_line(0))), 1.52, "satin")
    sh.flap_fill = M.hook(8).recolor({1: 0, 2: 2, 3: 0})


def sumska(sh: Shirt, rng: random.Random):
    bt = M.birds_tree()
    us = stack(
        (1, b_line(1)),
        (2, b_teeth(2, 0)),
        (1, None),
        (bt.h, b_repeat(bt, 2)),
        (1, None),
        (2, b_teeth(2, 0, flip=True)),
        (1, b_line(1)),
    )
    y = sh.ustavka(us, 62, 1.0)
    sh.gilce("sleeve", 28, y + 10, END - y - 10, 0.9)
    sh.bib(bt, bt.w, bt.h, 196, 1.4)
    side = rng.choice([M.small_star().recolor({3: 2}), M.small_rhomb()])
    sh.pazukha(column(side, gap=2, side=1), side.w + 4, 68, 190, 1.44, 26, point=False)
    sh.cuffs(
        stack((1, b_line(1)), (3, b_teeth(3, 0)), (3, b_teeth(3, 2, flip=True)), (1, b_line(1))),
        1.52,
    )
    sh.flap_fill = M.bird()


def ternopilska(sh: Shirt, rng: random.Random):
    borsh = R.borsh(rng.choice([(2, 4, 3), (3, 2, 4)]))

    y = sh.ustavka(
        stack((1, b_line(2)), (24, borsh), (1, b_line(2)), (1, None), (5, b_chain(2, 4))),
        58,
        1.44,
        "satin",
    )
    sh.stripes(
        lambda r, c: 2 if c in (0, 8) else borsh(r, c + 2),
        9,
        (-0.5, 0.5),
        y + 8,
        END,
        1.44,
        "satin",
    )
    sh.pazukha(
        _cells(lambda r, c: 2 if c in (0, 19) else borsh(r, c + 2), 20),
        20,
        68,
        286,
        1.52,
        34,
        tech="satin",
    )
    sh.cuffs(stack((1, b_line(2)), (9, borsh), (1, b_line(2))), 1.52, "satin")
    sh.flap_fill = M.kalyna_birds().recolor({0: 2, 3: 3, 4: 3})


def kharkivska(sh: Shirt, rng: random.Random):
    us = stack(
        (1, b_line(0)), (7, b_meander(2)), (1, b_line(0)), (1, None), (5, b_chain(0, 3)), (1, None),
        (1, b_line(0)), (7, b_meander(2)), (1, b_line(0)),
    )  # fmt: skip
    y = sh.ustavka(us, 60, 1.36)
    tree = M.tree(29, 47).recolor({0: 2})
    sh.column(tree, 0, y + 12, END, 1.16, gap=10)
    mea = b_meander(2)

    def col(r, c):
        if c < 11:
            return mea(c - 2, r) if 2 <= c < 9 else (0 if c in (0, 10) else None)
        return tree(r % 49, c - 11) if r % 49 < 47 and c - 11 < 29 else None

    if rng.random() < 0.5:
        sh.pazukha(_cells(col, 40), 40, 68, 286, 1.04, 34)
    else:
        sh.pazukha(column(tree, gap=2, side=0), tree.w + 4, 68, 286, 1.12, 34)
    sh.cuffs(stack((1, b_line(0)), (7, b_meander(2)), (1, b_line(0))), 1.52)
    sh.flap_fill = M.tree(19, 29).recolor({0: 2})


def khersonska(sh: Shirt, rng: random.Random):
    tree = M.tree(29, 47).recolor({0: 2})
    y = sh.ustavka(_band(tree, 0, 0, gap=4), 58, 1.04)
    for x in (16, 40):
        sh.gilce("sleeve", x, y + 10, END - y - 10, 0.75)
    sh.bib(M.birds_tree().recolor({0: 0, 2: 2, 3: 3}), 45, 27, 200, 1.4)
    side = rng.choice([M.small_star().recolor({0: 0, 3: 2}), M.small_rhomb().recolor({2: 2})])
    sh.pazukha(column(side, gap=2, side=0), side.w + 4, 68, 196, 1.44, 26, point=False)
    sh.cuffs(stack((1, b_line(0)), (6, b_chain(0, 2)), (1, b_line(0))), 1.52)
    sh.flap_fill = M.tree(19, 29).recolor({0: 2})


def khmelnytska(sh: Shirt, rng: random.Random):
    y = sh.ustavka(
        stack((1, b_line(2)), (24, R.saw), (1, b_line(2)), (1, None), (5, b_chain(0, 2))),
        60,
        1.36,
        "satin",
    )

    def stripe(r, c):
        if c in (0, 6) or abs(r % 8 - 4) == abs(c - 3):
            return 0
        return 3 if r % 8 == 4 and c == 3 else None

    sh.stripes(stripe, 7, (-0.45, 0.45), y + 10, END, 1.36)
    if rng.random() < 0.5:
        sh.pazukha(
            _cells(lambda r, c: 2 if c in (0, 21) else R.saw(r, c - 1), 22),
            22,
            68,
            286,
            1.44,
            34,
            tech="satin",
        )
    else:
        rh = M.rich(10, "rhomb").recolor({2: 2, 3: 3})
        sh.pazukha(column(rh, side=2), rh.w + 4, 68, 286, 1.28, 34)
    sh.cuffs(stack((8, R.saw), (1, b_line(2))), 1.6, "satin")
    sh.flap_fill = M.rich(8, "rhomb").recolor({2: 2, 3: 3})


def cherkaska(sh: Shirt, rng: random.Random):
    sh.bib(
        lambda r, c: 1 if r in (0, 73) or c in (0, 55) else R.lattice(r + 4, c - 1),
        56,
        74,
        66,
        1.28,
    )
    sh.stripes(lambda r, c: 1 if c in (0, 10) else R.lattice(r, c + 4), 11, (0,), 120, END, 1.28)
    sh.ustavka(stack((1, b_line(1)), (18, R.lattice), (1, b_line(1))), 60, 1.28)
    if rng.random() < 0.5:
        sh.cuffs(stack((1, b_line(1)), (9, lambda r, c: R.lattice(r + 4, c)), (1, b_line(1))), 1.52)
    else:
        sh.cuffs(stack((1, b_line(1)), (5, b_chain(0, 1)), (1, b_line(1))), 1.6)
    sh.flap_fill = _tiled(M.small_rhomb().recolor({2: 1, 1: 0}), 2, 2)


def chernivetska(sh: Shirt, rng: random.Random):
    hk = M.hook(9)
    us = stack(
        (1, b_line(1)),
        (2, b_line(0)),
        (1, None),
        (hk.h, b_repeat(hk, 1)),
        (1, None),
        (2, b_line(0)),
        (1, b_line(1)),
        (5, b_chain(2, 3)),
    )
    y = sh.ustavka(us, 58, 1.2)
    sh.scatter(M.rose(4), y + 16, END, 1.28, 40, n=2)
    vine = M.rose_vine()
    w = 34
    frame = {0: 0, 2: 1, w - 1: 0, w - 3: 1}

    def col(r, c):
        if c in frame:
            k = frame[c]
            return k if (k == 0 or r % 2 == 0) else None
        return vine(r % vine.h, c - 5) if 5 <= c < w - 5 else None

    if rng.random() < 0.7:
        sh.pazukha_columns(Pattern(col, w), 1.15)
    else:
        big = M.rich(11, "star").recolor({2: 2, 3: 3})
        sh.pazukha(column(big, side=0), big.w + 4, 68, 286, 1.28, 34)
    sh.cuffs(stack((2, b_line(0)), (5, b_chain(2, 3)), (2, b_line(0))), 1.52)
    sh.flap_fill = M.rose_branch()


def chernihivska(sh: Shirt, rng: random.Random):
    st = M.star(10)
    y = sh.ustavka(
        stack(
            (1, b_line(1)),
            (1, None),
            (st.h, b_repeat(st, 1)),
            (1, None),
            (1, b_line(1)),
            (5, b_chain(0, 1)),
        ),
        58,
        1.2,
    )
    sh.scatter(M.small_star(), y + 14, END, 1.44, 26, n=2)
    main = rng.choice([st, M.orlyk()])
    sh.pazukha(column(main, gap=1, side=1), main.w + 4, 68, 286, 1.36 if main is st else 1.28, 34)
    sh.cuffs(stack((1, b_line(1)), (7, b_repeat(M.small_star(), 2)), (1, b_line(1))), 1.52)
    sh.flap_fill = M.orlyk()


def _ornek_shirt(sh: Shirt, cols, vertical: bool):
    if vertical:
        for x in (14, 40):
            sh.ornek("sleeve", x, 100, END - 100, cols, 0.8)
    else:
        for i in range(3):
            for x in (14, 40):
                sh.ornek("sleeve", x, 96 + i * 66, 56, cols, 0.7)


def ar_krym(sh: Shirt, rng: random.Random):
    cols = ("#C9506B", "#4E8B5C", "#D9A441")
    sh.ustavka(
        stack((1, b_line(2)), (1, None), (5, b_chain(0, 2)), (1, None), (1, b_line(2))), 66, 1.44
    )
    _ornek_shirt(sh, cols, rng.random() < 0.7)
    for side in (-1, 1):
        for k in (0, 1):
            sh.ornek("body", 223.5 + side * (26 + k * 24), 72, 200, cols, 0.85)
    sh.cuffs(stack((1, b_line(2)), (5, b_chain(0, 3)), (1, b_line(2))), 1.6)
    sh.flap_fill = M.tree(19, 29).recolor({0: 0, 1: 1, 2: 2, 4: 4})


def m_kyiv(sh: Shirt, rng: random.Random):
    gr = M.grapes()
    y = sh.ustavka(_band(gr, 1, 3, gap=2), 56, 1.12)
    sh.column(M.small_star().recolor({3: 3}), 0, y + 14, END, 1.44, gap=20)
    main = rng.choice([gr, M.star(9).recolor({3: 3})])
    sh.pazukha(column(main, gap=2, side=1), main.w + 4, 68, 286, 1.28, 34)
    sh.cuffs(
        stack((1, b_line(1)), (7, b_repeat(M.small_star().recolor({3: 3}), 2)), (1, b_line(1))),
        1.52,
    )
    sh.flap_fill = gr


def m_sevastopol(sh: Shirt, rng: random.Random):
    cols = ("#2a4f7a", "#4E8B5C", "#D9A441")
    sh.ustavka(stack((1, b_line(2)), (5, b_wave(0, 5, 12)), (1, b_line(2))), 66, 1.44)
    _ornek_shirt(sh, cols, rng.random() < 0.3)
    for side in (-1, 1):
        sh.ornek("body", 223.5 + side * 32, 72, 200, cols, 0.9)
    sh.cuffs(stack((1, b_line(2)), (5, b_wave(0, 5, 12)), (1, b_line(2))), 1.6)
    sh.flap_fill = M.tree(19, 29).recolor({0: 2, 2: 3})


def generic(sh: Shirt, rng: random.Random):
    """Для регіону без власного рецепта: зірки на пазусі, ромби на уставці."""
    st = M.star(9)
    y = sh.ustavka(_band(M.small_rhomb(), 1, 0, gap=1), 60, 1.28)
    sh.scatter(M.small_star(), y + 14, END, 1.44, 30, n=2)
    sh.pazukha(column(st, gap=1, side=1), st.w + 4, 68, 286, 1.36, 34)
    sh.cuffs(stack((1, b_line(1)), (5, b_chain(0, 2)), (1, b_line(1))), 1.52)
    sh.flap_fill = st


# slug -> (код для id, палітра ролей, полотно, кольори шнурків, рецепт)
CHERNIVTSI_PALETTE = ["#c8202c", "#1b1714", "#e2b12a", "#2f8a3a", "#1d5a26", "#7d0f18", "#e04a52"]
REGIONS: dict[str, tuple[str, list[str], str, list[str], Recipe]] = {
    "vinnytska-oblast": (
        "vn",
        [BL, "#3a3431", CH, "#77706a", "#2e6b3a"],
        "#F6F3EC",
        ["#2a2522", CH],
        vinnytska,
    ),
    "volynska-oblast": (
        "vo",
        ["#bf2a2c", BL, "#23397f", "#d9a628", "#2e6b3a"],
        "#EEE8DC",
        ["#23397f", "#bf2a2c"],
        volynska,
    ),
    "dnipropetrovska-oblast": (
        "dp",
        ["#c8232c", BL, "#4f9fd0", "#e2b12a", "#2e6b3a"],
        "#F7F4EE",
        ["#c8232c", "#4f9fd0"],
        dnipropetrovska,
    ),
    "donetska-oblast": (
        "dn",
        ["#c62a2e", BL, "#2f4fa0", "#e2b12a", "#2e6b3a"],
        "#FAF8F3",
        ["#c62a2e", "#2f4fa0"],
        donetska,
    ),
    "zhytomyrska-oblast": (
        "zh",
        ["#c42a2a", BL, "#26397f", "#e2b12a", "#2f7a3b"],
        "#E9E3D6",
        ["#c42a2a", "#26397f"],
        zhytomyrska,
    ),
    "zakarpatska-oblast": (
        "zk",
        [CH, BL, "#d6a823", "#2e7d32", "#5B2C83"],
        "#F1ECE2",
        [CH, "#5B2C83"],
        zakarpatska,
    ),
    "zaporizka-oblast": (
        "zp",
        ["#c8232c", BL, "#d9a628", "#2a6d35", "#2a6d35"],
        "#FAF7F1",
        ["#c8232c", "#d9a628"],
        zaporizka,
    ),
    "ivano-frankivska-oblast": (
        "if",
        ["#c46210", "#5a1418", "#e2b12a", "#b8262b", "#2f6f3a"],
        "#F3EDE0",
        ["#c46210", "#b8262b"],
        ivano_frankivska,
    ),
    "kyivska-oblast": (
        "kv",
        ["#c41f2b", BL, "#e2b12a", "#c41f2b", "#2e6b3a"],
        "#FBF9F4",
        ["#c41f2b", BL],
        kyivska,
    ),
    "kirovohradska-oblast": (
        "kr",
        ["#c8232c", BL, "#d9a628", "#c8232c", "#2a6d35"],
        "#F8F5EF",
        ["#c8232c", "#d9a628"],
        kirovohradska,
    ),
    "luhanska-oblast": (
        "lh",
        ["#c62a2e", BL, "#5aa7d6", "#26397f", "#2e6b3a"],
        "#F6F3EC",
        ["#5aa7d6", "#c62a2e"],
        luhanska,
    ),
    "lvivska-oblast": (
        "lv",
        [BL, "#2a2420", "#c62a2e", "#d9a628", "#2e7d32"],
        "#F4EFE5",
        ["#c62a2e", BL],
        lvivska,
    ),
    "mykolaivska-oblast": (
        "mk",
        ["#c62a2e", BL, "#8A9BA8", "#d9a628", "#3e6a4a"],
        "#F7F4EE",
        ["#8A9BA8", "#c62a2e"],
        mykolaivska,
    ),
    "odeska-oblast": (
        "od",
        ["#c62a2e", BL, "#d9a628", "#26397f", "#2e6b3a"],
        "#F8F5EF",
        ["#d9a628", "#c62a2e"],
        odeska,
    ),
    "poltavska-oblast": (
        "pl",
        ["#ffffff", "#c9c2b6", "#e8e2d8", "#b7ae9f", "#d8d1c4"],
        "#E9E4DA",
        ["#ffffff", "#d8d1c4"],
        poltavska,
    ),
    "rivnenska-oblast": (
        "rv",
        ["#c33a32", "#8f2620", "#6f8fbf", "#c33a32", "#c33a32"],
        "#ECE6DA",
        ["#c33a32"],
        rivnenska,
    ),
    "sumska-oblast": (
        "sm",
        ["#c62a2e", BL, "#26397f", "#d9a628", "#2e6b3a"],
        "#F2EEE6",
        ["#26397f", "#c62a2e"],
        sumska,
    ),
    "ternopilska-oblast": (
        "tr",
        [BL, "#120f0d", "#b8262b", "#2e7d32", "#d9a628"],
        "#F6F3EC",
        [BL, "#b8262b"],
        ternopilska,
    ),
    "kharkivska-oblast": (
        "kh",
        [BL, "#2a2420", "#c62a2e", "#d9a628", "#2a6d35"],
        "#F5F1E9",
        ["#c62a2e", BL],
        kharkivska,
    ),
    "khersonska-oblast": (
        "ks",
        [BL, "#2a2420", "#d9a628", "#5aa7d6", "#2a6d35"],
        "#F2EEE6",
        ["#d9a628", "#5aa7d6"],
        khersonska,
    ),
    "khmelnytska-oblast": (
        "km",
        [BL, "#2a2420", "#c62a2e", "#26397f", "#d9a628"],
        "#F6F3EC",
        [BL, "#c62a2e"],
        khmelnytska,
    ),
    "cherkaska-oblast": (
        "ck",
        ["#c41f2b", BL, "#c41f2b", "#c41f2b", "#c41f2b"],
        "#FAF8F3",
        ["#c41f2b", BL],
        cherkaska,
    ),
    "chernivetska-oblast": (
        "cv",
        CHERNIVTSI_PALETTE,
        "#F7F4EE",
        ["#c0262d", "#e2b12a"],
        chernivetska,
    ),
    "chernihivska-oblast": (
        "cg",
        ["#c22a2f", BL, "#c22a2f", "#c22a2f", "#2e6b3a"],
        "#F7F4EE",
        ["#c22a2f"],
        chernihivska,
    ),
    "ar-krym": (
        "cr",
        ["#C9506B", "#7a2d3f", "#D9A441", "#4E8B5C", "#4E8B5C"],
        "#F4EEE4",
        ["#C9506B", "#D9A441"],
        ar_krym,
    ),
    "m-kyiv": (
        "mkv",
        ["#c41f2b", BL, "#5B2C83", "#d9a628", "#3a7d2c"],
        "#FBF9F4",
        ["#5B2C83", "#c41f2b"],
        m_kyiv,
    ),
    "m-sevastopol": (
        "sv",
        ["#2a4f7a", "#1c3350", "#D9A441", "#C9506B", "#4E8B5C"],
        "#F2ECE2",
        ["#D9A441", "#2a4f7a"],
        m_sevastopol,
    ),
}

GENERIC_PALETTE = ["#c41f2b", BL, "#e2b12a", "#26397f", "#2e6b3a"]


def build_shirt(slug: str, rng: random.Random, fallback_colors: list[str] | None = None) -> Shirt:
    if slug in REGIONS:
        code, palette, linen, ties, recipe = REGIONS[slug]
    else:
        palette = _fallback_palette(fallback_colors)
        code, linen, ties, recipe = "gn", "#F7F4EE", [palette[0]], generic
    sh = Shirt(list(palette), linen, rng.choice(ties), pid=f"v{code}{rng.getrandbits(20):x}")
    recipe(sh, rng)
    sh.flap(sh.flap_fill or M.star(9))
    return sh


def _fallback_palette(colors: list[str] | None) -> list[str]:
    usable = [c for c in (colors or []) if c.upper() not in ("#FFFFFF", "#FFF")]
    pal = list(GENERIC_PALETTE)
    for i, c in enumerate(usable[:2]):
        pal[(0, 2)[i]] = c
    return pal
