"""Каталог мотивів: назви, прив'язка до сторінки «Символи» і набори мотивів кожного регіону.

Набори повторюють те, що реально малюють рецепти в regions.py (включно з варіантами за датою).
Під плиткою - лише назва мотиву; тлумачення з джерелами - на сторінці «Символи».
"""

from collections.abc import Callable
from functools import cache

from . import motifs as M
from . import regional as R
from .grid import Pattern, b_chain, b_kryv, b_meander, b_teeth, b_wave, stack
from .regions import REGIONS, build_shirt
from .tiles import smooth_tile, stitch_tile

# ключ -> (назва uk, назва en, якір на сторінці «Символи» або "")
NAMES = {
    "star": ("Восьмипелюсткова зірка", "Eight-petal star", "symbol-zirka"),
    "hook": ("Ромб із ріжками", "Rhombus with hooks", "symbol-romb"),
    "rich_star": ("Великий ромб із зіркою", "Large rhombus with a star", "symbol-romb"),
    "rich_rhomb": ("Ромб у ромбі", "Rhombus within a rhombus", "symbol-romb"),
    "rose": ("Троянда", "Rose", "symbol-ruzha"),
    "rose_vine": ("Троянди на стеблі", "Roses on a stem", "symbol-ruzha"),
    "rose_branch": ("Гілка з трояндами", "Rose branch", "symbol-ruzha"),
    "tree": ("Дерево життя у вазоні", "Tree of life in a vase", "symbol-derevo"),
    "tree_free": ("Дерево життя", "Tree of life", "symbol-derevo"),
    "lily": ("Квітка у вазоні", "Flower in a vase", "symbol-vazon"),
    "kalyna": ("Калина", "Guelder rose (kalyna)", "symbol-kalyna"),
    "kalyna_birds": ("Калина з пташками", "Kalyna with birds", "symbol-kalyna"),
    "grapes": ("Виноградне гроно", "Grape cluster", "symbol-vynohrad"),
    "oak": ("Дубове листя з жолудями", "Oak leaves with acorns", "symbol-sosonka"),
    "sosonka": ("Сосонка", "Sosonka (pine sprig)", "symbol-sosonka"),
    "sun": ("Коло з розеткою", "Circle with a rosette", "symbol-sontse"),
    "periwinkle": ("Барвінок", "Periwinkle", ""),
    "branch": ("Гілка з листям", "Leafy branch", ""),
    "bird": ("Птах", "Bird", "symbol-ptakh"),
    "birds_tree": ("Птахи біля дерева", "Birds by a tree", "symbol-ptakh"),
    "orlyk": ("Двоголовий орел (орлик)", "Double-headed eagle", "symbol-orel"),
    "cross": ("Хрест", "Cross", "symbol-khrest"),
    "crown": ("Корона", "Crown", ""),
    "small_star": ("Зірочка", "Small star", "symbol-zirka"),
    "small_rhomb": ("Ромбик", "Small rhombus", "symbol-romb"),
    "curly_vine": ("Кучерява гілка", "Curly sprig", ""),
    "nyz": ("Чорна низь", "Black nyz", ""),
    "borsh": ("Борщівські ромбики на чорному", "Borshchiv rhombuses on black", "symbol-romb"),
    "lattice": ("Ромбова сітка з зірками", "Rhombus lattice with stars", "symbol-romb"),
    "squares": ("Кольорові квадрати", "Coloured squares", ""),
    "saw": ("Зубчасті лінії", "Saw-tooth lines", ""),
    "chevron": ("Шеврони", "Chevrons", ""),
    "zavolikannia": ("Заволікання", "Zavolikannia (woven-look stitch)", ""),
    "kryvulka": ("Кривулька", "Kryvulka (zigzag)", "symbol-kryvulka"),
    "kryv_rows": ("Кольорові кривульки", "Coloured kryvulkas", "symbol-kryvulka"),
    "chain": ("Ланцюжок ромбиків", "Chain of rhombuses", "symbol-romb"),
    "teeth": ("Зубці", "Teeth", ""),
    "wave": ("Хвиля", "Wave", ""),
    "meander": ("Меандр", "Meander", ""),
    "gilce": ("Ламане гільце", "Broken branch (hilce)", ""),
    "ornek": ("Орьнек: тюльпани й лоза", "Ornek: tulips and vine", "ornek"),
    "knots": ("Кучерики", "Kucheryky (curly knots)", ""),
}

GROUPS = (
    ("main", "Пазуха й комір", "Chest and collar"),
    ("sleeve", "Рукав", "Sleeve"),
    ("border", "Бордюри", "Borders"),
)

# (група, ключ, фабрика -> (візерунок, ширина, висота, техніка) або назва гладі)
Entry = tuple[str, str, Callable[[], tuple]]


def _m(p: Pattern, tech="x"):
    return lambda: (p, p.w, p.h, tech)


def _fill(fn, w=24, h=24, tech="x"):
    return lambda: (Pattern(fn), w, h, tech)


def _band(fn, h, w=30, tech="x"):
    return lambda: (Pattern(fn), w, h, tech)


def _smooth(kind):
    return lambda: kind


TEETH = stack((3, b_teeth(3, 0)), (3, b_teeth(3, 1, flip=True)))
CHAIN = b_chain(0, 2)
KRYV = b_kryv(5, 0)
WAVE = b_wave(0, 5, 10)

REGION_MOTIFS: dict[str, list[Entry]] = {
    "vinnytska-oblast": [
        ("main", "rich_rhomb", _m(M.rich(10, "rhomb").recolor({2: 3, 3: 2}))),
        ("main", "rich_star", _m(M.rich(10, "star").recolor({2: 3, 3: 2}))),
        ("sleeve", "nyz", _band(R.nyz, 17, 36, "satin")),
        ("sleeve", "curly_vine", _fill(R.curly_vine, 13, 28)),
    ],
    "volynska-oblast": [
        ("main", "star", _m(M.star(10))),
        ("main", "hook", _m(M.hook(9))),
        ("border", "chain", _band(CHAIN, 5)),
        ("border", "teeth", _band(TEETH, 6)),
    ],
    "dnipropetrovska-oblast": [
        ("main", "lily", _m(M.lily().recolor({4: 2}))),
        ("main", "sun", _m(M.sun(10))),
        ("sleeve", "small_star", _m(M.small_star().recolor({3: 2}))),
        ("border", "wave", _band(WAVE, 5)),
    ],
    "donetska-oblast": [
        ("main", "tree", _m(M.tree(31, 49))),
        ("main", "lily", _m(M.lily().recolor({4: 4}))),
        ("sleeve", "rose", _m(M.rose(4))),
        ("border", "teeth", _band(TEETH, 6)),
    ],
    "zhytomyrska-oblast": [
        ("main", "hook", _m(M.hook(9))),
        ("main", "star", _m(M.star(9))),
        ("sleeve", "periwinkle", _m(M.periwinkle().recolor({0: 2, 3: 3}))),
        ("border", "chain", _band(CHAIN, 5)),
    ],
    "zakarpatska-oblast": [
        ("main", "kryv_rows", _fill(R.kryv_rows(), 24, 30)),
        ("border", "kryvulka", _band(KRYV, 5)),
        ("border", "chain", _band(b_chain(3, 2), 5)),
    ],
    "zaporizka-oblast": [
        ("main", "sun", _m(M.sun(10))),
        ("main", "kalyna", _m(M.kalyna())),
        ("border", "small_star", _m(M.small_star().recolor({3: 2}))),
    ],
    "ivano-frankivska-oblast": [
        ("main", "chevron", _fill(R.chevron, 20, 24)),
        ("main", "hook", _m(M.hook(8))),
        ("sleeve", "knots", _smooth("knots")),
        ("sleeve", "small_rhomb", _m(M.small_rhomb())),
    ],
    "kyivska-oblast": [
        ("main", "branch", _m(M.branch(39))),
        ("main", "grapes", _m(M.grapes().recolor({2: 0, 4: 1}))),
    ],
    "kirovohradska-oblast": [
        ("main", "tree", _m(M.tree(31, 49))),
        ("main", "lily", _m(M.lily().recolor({4: 4}))),
        ("border", "rose", _m(M.rose(5))),
    ],
    "luhanska-oblast": [
        ("main", "squares", _fill(R.squares, 22, 22)),
        ("main", "lily", _m(M.lily().recolor({4: 2}))),
        ("sleeve", "small_star", _m(M.small_star().recolor({3: 2}))),
    ],
    "lvivska-oblast": [
        ("main", "sosonka", _m(M.sosonka(24).recolor({0: 2}))),
        ("border", "teeth", _band(stack((3, b_teeth(3, 4)), (3, b_teeth(3, 1, flip=True))), 6)),
        ("border", "kryvulka", _band(b_kryv(5, 2), 5)),
    ],
    "mykolaivska-oblast": [
        ("main", "oak", _m(M.oak())),
        ("main", "sosonka", _m(M.sosonka(24))),
        ("border", "wave", _band(b_wave(2, 5, 10), 5)),
    ],
    "odeska-oblast": [
        ("main", "orlyk", _m(M.orlyk().recolor({0: 1, 1: 1, 2: 2, 3: 0}))),
        ("main", "cross", _m(M.cross())),
        ("border", "crown", _m(M.crown())),
    ],
    "poltavska-oblast": [
        ("main", "star", _m(M.star(9).recolor({1: 3, 2: 1, 3: 0}))),
        ("main", "rich_rhomb", _m(M.rich(10, "rhomb").recolor({1: 3, 2: 1, 3: 2}))),
        ("sleeve", "gilce", _smooth("gilce")),
    ],
    "rivnenska-oblast": [
        ("main", "rich_star", _m(M.rich(11, "star").recolor({1: 0, 2: 0, 3: 2}))),
        ("main", "hook", _m(M.hook(9).recolor({1: 0, 2: 2, 3: 0}))),
        ("border", "zavolikannia", _fill(R.zavolikannia, 30, 20, "satin")),
    ],
    "sumska-oblast": [
        ("main", "birds_tree", _m(M.birds_tree())),
        ("main", "bird", _m(M.bird())),
        ("sleeve", "gilce", _smooth("gilce")),
    ],
    "ternopilska-oblast": [
        ("main", "borsh", _fill(R.borsh(), 24, 24, "satin")),
        ("main", "kalyna_birds", _m(M.kalyna_birds().recolor({0: 2, 3: 3, 4: 3}))),
        ("border", "chain", _band(b_chain(2, 4), 5)),
    ],
    "kharkivska-oblast": [
        ("main", "tree", _m(M.tree(29, 47).recolor({0: 2}))),
        ("border", "meander", _band(b_meander(2), 7, 32)),
    ],
    "khersonska-oblast": [
        ("main", "birds_tree", _m(M.birds_tree().recolor({0: 0, 2: 2, 3: 3}))),
        ("main", "tree", _m(M.tree(29, 47).recolor({0: 2}))),
        ("sleeve", "gilce", _smooth("gilce")),
    ],
    "khmelnytska-oblast": [
        ("main", "saw", _fill(R.saw, 24, 24, "satin")),
        ("main", "rich_rhomb", _m(M.rich(10, "rhomb").recolor({2: 2, 3: 3}))),
    ],
    "cherkaska-oblast": [
        ("main", "lattice", _fill(R.lattice, 36, 36)),
        ("main", "small_rhomb", _m(M.small_rhomb().recolor({2: 1, 1: 0}))),
        ("border", "chain", _band(b_chain(0, 1), 5)),
    ],
    "chernivetska-oblast": [
        ("main", "rose_vine", lambda: (M.rose_vine(), 24, 52, "x")),
        ("main", "rose_branch", _m(M.rose_branch())),
        ("main", "rich_star", _m(M.rich(11, "star").recolor({2: 2, 3: 3}))),
        ("sleeve", "hook", _m(M.hook(9))),
        ("sleeve", "rose", _m(M.rose(4))),
    ],
    "chernihivska-oblast": [
        ("main", "star", _m(M.star(10))),
        ("main", "orlyk", _m(M.orlyk())),
        ("sleeve", "small_star", _m(M.small_star())),
    ],
    "ar-krym": [
        ("main", "ornek", _smooth("ornek")),
        ("main", "tree_free", _m(M.tree(19, 29))),
        ("border", "chain", _band(CHAIN, 5)),
    ],
    "m-kyiv": [
        ("main", "grapes", _m(M.grapes())),
        ("main", "star", _m(M.star(9).recolor({3: 3}))),
        ("sleeve", "small_star", _m(M.small_star().recolor({3: 3}))),
    ],
    "m-sevastopol": [
        ("main", "ornek", _smooth("ornek")),
        ("main", "tree_free", _m(M.tree(19, 29).recolor({0: 2, 2: 3}))),
        ("border", "wave", _band(WAVE, 5)),
    ],
}


def palette(slug: str) -> list[str]:
    return list(REGIONS[slug][1])


@cache
def flap_motif(slug: str) -> Pattern:
    """Мотив із кінців коміра (мотив регіону з бази) - для мапи."""
    import random

    return build_shirt(slug, random.Random(0)).flap_fill or M.star(9)


# орьнек і «кучерики» мають власні кольори ниток
SMOOTH_COLORS = {
    ("ar-krym", "ornek"): ["#C9506B", "#4E8B5C", "#D9A441"],
    ("m-sevastopol", "ornek"): ["#2a4f7a", "#4E8B5C", "#D9A441"],
}


def _smooth_palette(slug, key):
    pal = palette(slug)
    if (slug, key) in SMOOTH_COLORS:
        return SMOOTH_COLORS[(slug, key)]
    if key == "knots":
        return [pal[3], pal[0], pal[2]]
    return pal


def motif_tile(slug: str, key: str, factory, lang: str, pid: str, css="") -> str:
    name = NAMES[key][1 if lang == "en" else 0]
    made = factory()
    if isinstance(made, str):
        return smooth_tile(made, _smooth_palette(slug, key), name, pid, css)
    pattern, w, h, tech = made
    return stitch_tile(pattern, palette(slug), name, pid, w, h, tech, css)


@cache
def region_tiles(slug: str, lang: str) -> tuple:
    """Групи плиток для сторінки регіону: ((назва групи, ((svg, назва, якір), ...)), ...)."""
    entries = REGION_MOTIFS.get(slug)
    if not entries:
        return ()
    out = []
    for group, title_uk, title_en in GROUPS:
        tiles = []
        for i, (g, key, factory) in enumerate(entries):
            if g != group:
                continue
            pid = f"t{REGIONS[slug][0]}{i}"
            svg = motif_tile(slug, key, factory, lang, pid, "vd-motif__art")
            name_uk, name_en, anchor = NAMES[key]
            tiles.append((svg, name_en if lang == "en" else name_uk, anchor))
        if tiles:
            out.append((title_en if lang == "en" else title_uk, tuple(tiles)))
    return tuple(out)
