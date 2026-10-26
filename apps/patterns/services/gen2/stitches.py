"""Збирання стібків у компактний SVG.

Хрестики однієї сітки й кольору - один path (кожен стібок - підшлях),
а шари «тінь / нижній стібок / верхній стібок / відблиск» - <use> цього path з різним штрихом.
Обрізання кінців стібка - stroke-dasharray (пунктир починається наново з кожного підшляху).
"""

import math
from collections import defaultdict

from .colors import shade

THREAD = 0.42
SQ2 = math.sqrt(2)
# видима частина діагоналі клітинки: від 0.14 до 0.86
_VIS, _GAP = 0.72 * SQ2, 0.28 * SQ2
CROSS_DASH = (
    f'stroke-dasharray="{_VIS:.4f} {_GAP:.4f}" stroke-dashoffset="{_VIS + _GAP - 0.14 * SQ2:.4f}"'
)
_HL_VIS = 0.255
HL_DASH = f'stroke-dasharray="{_HL_VIS} {SQ2 - _HL_VIS:.4f}" stroke-dashoffset="{SQ2 - 0.48:.4f}"'
VARIANT_SHADES = (0.0, 0.08, -0.07)


def _num(v: float) -> str:
    s = f"{v:.2f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def _variant(c: int, r: int) -> int:
    return (0, 0, 1, 2)[(c * 7 + r * 13) % 4]


class Layer:
    """Стібки однієї області (тулуб, рукав, манжет, комір) у її координатах."""

    def __init__(self):
        # (s, ox, oy) -> (k, v) -> [(c, r)]
        self.crosses = defaultdict(lambda: defaultdict(list))
        # (s, ox, oy) -> (k, v) -> [(c, r, n)]
        self.satin = defaultdict(lambda: defaultdict(list))
        # (s, k, v) -> [(cx, cy, angle)]
        self.free = defaultdict(list)
        self.knots = []
        self.raw = []

    @staticmethod
    def grid_key(x0: float, y0: float, s: float):
        ox, oy = round(x0 % s, 3), round(y0 % s, 3)
        if abs(ox - s) < 1e-3:
            ox = 0.0
        if abs(oy - s) < 1e-3:
            oy = 0.0
        return (round(s, 4), ox, oy), round((x0 - ox) / s), round((y0 - oy) / s)

    def add_cross(self, key, c: int, r: int, k: int):
        self.crosses[key][(k, _variant(c, r))].append((c, r))

    def add_satin(self, key, c: int, r: int, n: int, k: int):
        self.satin[key][(k, _variant(c, r))].append((c, r, n))

    def add_free_cross(self, cx: float, cy: float, s: float, angle: float, k: int):
        self.free[(round(s, 3), k, _variant(round(cx), round(cy)))].append((cx, cy, angle))

    def add_knot(self, x: float, y: float, r: float, k: int):
        self.knots.append((x, y, r, k, _variant(round(x), round(y))))


def _cross_paths(cells):
    """Два path: нижні «\\» і верхні «/» діагоналі, відносні переходи між стібками."""
    cells = sorted(set(cells), key=lambda p: (p[1], p[0]))
    back, front = [], []
    prev = None
    for c, r in cells:
        if prev is None:
            back.append(f"M{c} {r}l1 1")
            front.append(f"M{c + 1} {r}l-1 1")
        else:
            pc, pr = prev
            back.append(f"m{c - pc - 1} {r - pr - 1}l1 1")
            front.append(f"m{c - pc + 1} {r - pr - 1}l-1 1")
        prev = (c, r)
    return "".join(back), "".join(front)


def _satin_path(runs):
    runs = sorted(runs, key=lambda p: (p[1], p[0]))
    out, end = [], None
    for c, r, n in runs:
        if end is None:
            out.append(f"M{_num(c + 0.5)} {_num(r + 0.5)}h{n - 1}")
        else:
            out.append(f"m{c - end[0]} {r - end[1]}h{n - 1}")
        end = (c + n - 1, r)
    return "".join(out)


class StitchWriter:
    """Перетворює шари на SVG; спільні defs збирає в одному місці."""

    def __init__(self, pid: str, palette: list[str]):
        self.pid, self.pal = pid, palette
        self.defs: list[str] = []
        self.knot_symbols: set[tuple[int, int]] = set()
        self._n = 0

    def _id(self) -> str:
        self._n += 1
        return f"{self.pid}p{self._n}"

    def color(self, k: int, v: int) -> str:
        base = self.pal[k % len(self.pal)]
        return shade(base, VARIANT_SHADES[v]) if v else base

    def layer(self, layer: Layer) -> str:
        out = []
        for key, groups in layer.crosses.items():
            out.append(self._cross_block(key, groups))
        for key, groups in layer.satin.items():
            out.append(self._satin_block(key, groups))
        if layer.free:
            out.append(self._free_crosses(layer.free))
        out.extend(layer.raw)
        for x, y, r, k, v in layer.knots:
            self.knot_symbols.add((k, v))
            out.append(
                f'<use href="#{self.pid}k{k}{v}" transform="translate({_num(x)} {_num(y)}) scale({_num(r)})"/>'
            )
        return "".join(out)

    def _cross_block(self, key, groups) -> str:
        s, ox, oy = key
        refs = []
        for (k, v), cells in sorted(groups.items()):
            back, front = _cross_paths(cells)
            bid, fid = self._id(), self._id()
            self.defs.append(f'<path id="{bid}" d="{back}"/><path id="{fid}" d="{front}"/>')
            refs.append((self.color(k, v), bid, fid))
        w = THREAD
        shadow = "".join(
            f'<use href="#{b}" stroke="{shade(c, -0.5)}"/><use href="#{f}" stroke="{shade(c, -0.5)}"/>'
            for c, b, f in refs
        )
        backs = "".join(f'<use href="#{b}" stroke="{shade(c, -0.1)}"/>' for c, b, _ in refs)
        fronts = "".join(f'<use href="#{f}" stroke="{c}"/>' for c, _, f in refs)
        lights = "".join(f'<use href="#{f}" stroke="{shade(c, 0.5)}"/>' for c, _, f in refs)
        return (
            f'<g transform="translate({_num(ox)} {_num(oy)}) scale({s:g})" fill="none" '
            f'stroke-linecap="round">'
            f'<g stroke-width="{w * 1.42:.3f}" {CROSS_DASH}>{shadow}</g>'
            f'<g stroke-width="{w}" {CROSS_DASH}>{backs}{fronts}</g>'
            f'<g stroke-width="{w * 0.3:.3f}" {HL_DASH} opacity=".6" '
            f'transform="translate(-.05 -.05)">{lights}</g></g>'
        )

    def _satin_block(self, key, groups) -> str:
        s, ox, oy = key
        refs = []
        for (k, v), runs in sorted(groups.items()):
            pid = self._id()
            self.defs.append(f'<path id="{pid}" d="{_satin_path(runs)}"/>')
            base = self.pal[k % len(self.pal)]
            refs.append((shade(base, (0.0, 0.04, -0.04)[v]), pid))
        dark = "".join(f'<use href="#{p}" stroke="{shade(c, -0.45)}"/>' for c, p in refs)
        main = "".join(f'<use href="#{p}" stroke="{c}"/>' for c, p in refs)
        light = "".join(f'<use href="#{p}" stroke="{shade(c, 0.45)}"/>' for c, p in refs)
        return (
            f'<g transform="translate({_num(ox)} {_num(oy)}) scale({s:g})" fill="none">'
            f'<g stroke-width=".84" stroke-linecap="round">{dark}</g>'
            f'<g stroke-width=".58" stroke-linecap="round">{main}</g>'
            f'<g stroke-width=".13" opacity=".55" transform="translate(0 -.19)">{light}</g></g>'
        )

    def _free_crosses(self, free) -> str:
        """Хрестики під кутом (уздовж кривих): кінці стібків рахуються одразу."""
        out = []
        for (s, k, v), items in sorted(free.items()):
            c = self.color(k, v)
            h = 0.36 * s
            back, front, light = [], [], []
            for cx, cy, a in items:
                ca, sa = math.cos(a), math.sin(a)

                def pt(dx, dy, cx=cx, cy=cy, ca=ca, sa=sa):
                    return f"{cx + dx * ca - dy * sa:.2f} {cy + dx * sa + dy * ca:.2f}"

                back.append(f"M{pt(-h, -h)}L{pt(h, h)}")
                front.append(f"M{pt(h, -h)}L{pt(-h, h)}")
                light.append(f"M{pt(0.12 * s, -0.2 * s)}L{pt(-0.06 * s, -0.02 * s)}")
            w = THREAD * s
            b, f = "".join(back), "".join(front)
            out.append(
                f'<g fill="none" stroke-linecap="round">'
                f'<path d="{b}{f}" stroke="{shade(c, -0.5)}" stroke-width="{w * 1.42:.2f}"/>'
                f'<path d="{b}" stroke="{shade(c, -0.1)}" stroke-width="{w:.2f}"/>'
                f'<path d="{f}" stroke="{c}" stroke-width="{w:.2f}"/>'
                f'<path d="{"".join(light)}" stroke="{shade(c, 0.5)}" stroke-width="{w * 0.3:.2f}" '
                f'opacity=".6"/></g>'
            )
        return "".join(out)

    def knot_defs(self) -> str:
        out = []
        for k, v in sorted(self.knot_symbols):
            c = self.color(k, v)
            out.append(
                f'<g id="{self.pid}k{k}{v}"><circle r="1.02" fill="{shade(c, -0.55)}"/>'
                f'<circle cx="-.08" cy="-.1" r=".86" fill="{c}"/>'
                f'<path d="M-.55-.05a.55.55 0 0 1 .7-.45" stroke="{shade(c, 0.5)}" '
                f'stroke-width=".2" fill="none" opacity=".75" stroke-linecap="round"/></g>'
            )
        return "".join(out)
