"""Розміщення вишивки на сорочці: пазуха, уставка, поли рукава, манжети, кінці коміра."""

import math

from . import geometry as G
from .colors import shade
from .grid import BIG, Pattern, stack
from .stitches import Layer

LAYERS = ("body", "sleeve", "cuff", "flap")
SLEEVE_END = G.SL_LEN - 26


class Shirt:
    """Вишивка однієї сорочки. Палітра - ролі кольорів (див. grid.py)."""

    def __init__(self, palette: list[str], linen: str, tie: str | None = None, pid: str = "vd"):
        self.pal, self.linen, self.pid = palette, linen, pid
        self.tie = tie or palette[0]
        self.layers = {name: Layer() for name in LAYERS}
        self.flap_fill: Pattern | None = None

    # ---------- базове заповнення сітки ----------
    def field(self, fn, x0, y0, cols, rows, s, tech="x", layer="body", c0=0, cmin=None, cmax=None):
        lay = self.layers[layer]
        if layer in ("sleeve", "cuff"):
            # у рукаві все на спільній сітці: менше окремих блоків у SVG
            key, cb, rb = (round(s, 4), 0.0, 0.0), round(x0 / s), round(y0 / s)
        else:
            key, cb, rb = Layer.grid_key(x0, y0, s)
        for r in range(rows):
            lo = cmin(r) if cmin else 0
            hi = cmax(r) if cmax else cols
            if tech == "satin":
                c = lo
                while c < hi:
                    k = fn(r, c + c0)
                    if k is None:
                        c += 1
                        continue
                    n = 1
                    while c + n < hi and n < 6 and fn(r, c + n + c0) == k:
                        n += 1
                    lay.add_satin(key, cb + c, rb + r, n, k)
                    c += n
            else:
                for c in range(lo, hi):
                    k = fn(r, c + c0)
                    if k is not None:
                        lay.add_cross(key, cb + c, rb + r, k)

    def motif(self, m: Pattern, cx, y0, s, layer="body", tech="x"):
        self.field(m, cx - m.w * s / 2, y0, m.w, m.h, s, tech, layer)

    # ---------- рукав ----------
    @staticmethod
    def sleeve_at(y):
        left, right = G.sleeve_extent(y)
        return (left + right) / 2, (right - left) / 2, left, right

    def ustavka(self, band: Pattern, y0, s, tech="x", inner=2.0):
        """Поперечна смуга на рукаві від краю до краю."""
        rows = band.h
        cm = sum(self.sleeve_at(y0 + r * s + s / 2)[0] for r in range(rows)) / rows
        for r in range(rows):
            _, _, left, right = self.sleeve_at(y0 + r * s + s / 2)
            lo = math.floor((left - 3 - cm) / s)
            hi = math.floor((right - inner - cm) / s)
            self.field(
                lambda _r, c, r=r, lo=lo: band(r, c + lo + BIG),
                cm + (lo - 0.5) * s,
                y0 + r * s,
                hi - lo,
                1,
                s,
                tech,
                "sleeve",
            )
        return y0 + rows * s

    def stripes(self, fn, width, fracs, y0, y1, s, tech="x"):
        """Вертикальні смуги вздовж рукава (fracs - положення від осі, -1..1)."""
        for r in range(int((y1 - y0) / s)):
            y = y0 + r * s
            cm, hw, left, right = self.sleeve_at(y + s / 2)
            for f in fracs:
                x0 = cm + f * hw - width * s / 2
                if x0 < left - 3 or x0 + width * s > right - 1.5:
                    continue
                self.field(lambda _r, c, r=r: fn(r, c), x0, y, width, 1, s, tech, "sleeve")

    def column(self, m: Pattern, frac, y0, y1, s, gap=4, tech="x"):
        y = y0
        while y + m.h * s <= y1:
            cm, hw, _, _ = self.sleeve_at(y + m.h * s / 2)
            self.motif(m, cm + frac * hw, y, s, "sleeve", tech)
            y += m.h * s + gap

    def scatter(self, m: Pattern, y0, y1, s, dy, n=3):
        """Розсип мотивів у шаховому порядку."""
        y, i = y0, 0
        while y + m.h * s <= y1:
            _, hw, left, _ = self.sleeve_at(y + m.h * s / 2)
            span = 2 * hw - m.w * s - 8
            for j in range(n if i % 2 == 0 else n - 1):
                f = (j + (0.5 if i % 2 else 0)) / max(n - 1, 1)
                self.motif(m, left + 4 + m.w * s / 2 + span * f, y, s, "sleeve")
            y += dy
            i += 1

    def knot_rows(self, y0, rows, step, roles):
        """Гуцульські «кучерики» рядами через увесь рукав."""
        for i in range(rows):
            y = y0 + i * step * 0.9
            _, _, left, right = self.sleeve_at(y)
            x = left + 1 + (step / 2 if i % 2 else 0)
            j = 0
            while x < right - 2.5:
                self.layers["sleeve"].add_knot(x, y, step * 0.48, roles[(j + i // 2) % len(roles)])
                x += step
                j += 1
        return y0 + rows * step * 0.9

    def knot(self, x, y, r, k):
        self.layers["body"].add_knot(x, y, r, k)

    # ---------- тулуб ----------
    def pazukha(self, fn: Pattern, width, y0, y1, s, off, point=True, tech="x", strip=None):
        """Дві колони обабіч розрізу; низ загострений."""
        rows = int((y1 - y0) / s)
        half = width // 2

        def cut(r):
            return 0 if not point or r < rows - half else r - (rows - half) + 1

        for side in (-1, 1):
            x0 = G.AXC + side * off - width * s / 2
            self.field(fn, x0, y0, width, rows, s, tech, cmin=cut, cmax=lambda r: width - cut(r))
        if strip is not None:
            sfn, sw, sy1 = strip
            for side in (-1, 1):
                x0 = G.AXC + side * (sw * s / 2 + 2.2) - sw * s / 2
                self.field(sfn, x0, y0 + 2, sw, int((sy1 - y0) / s), s, tech)

    def pazukha_columns(self, fn: Pattern, s, y0=64.0, y1=286.0, off=32.4):
        """Пазуха як на еталоні: дві прямі колони з бордюром унизу."""
        w = fn.w
        rows = int((y1 - y0) / s)
        for side in (-1, 1):
            x0 = G.AXC + side * off - w * s / 2
            self.field(fn, x0, y0, w, rows, s)
            self.field(
                lambda r, c: 0 if r in (0, 2) else (1 if r == 1 and c % 2 == 0 else None),
                x0,
                y0 + rows * s,
                w,
                3,
                s,
            )

    def bib(self, fn, cols, rows, y0, s, tech="x"):
        self.field(fn, G.AXC - cols * s / 2, y0, cols, rows, s, tech)

    def hem(self, band: Pattern, s, tech="x"):
        cols = int(198 / s)
        self.field(
            band,
            G.AXC - cols * s / 2,
            404 - band.h * s,
            cols,
            band.h,
            s,
            tech,
            c0=-(cols // 2) + BIG,
        )

    def cuffs(self, band: Pattern, s, tech="x"):
        rows = band.h
        cols = int((G.CUFF_W - 3) / s)
        y0 = G.SL_LEN + G.CUFF_H / 2 - rows * s / 2
        x0 = G.CUFF_X + 1.5 + (G.CUFF_W - 3 - cols * s) / 2
        self.field(band, x0, y0, cols, rows, s, tech, "cuff", c0=-(cols // 2) + BIG)

    # ---------- кінці коміра ----------
    def curve_band(self, band: Pattern, pts, s, layer="flap"):
        """Бордюр уздовж ламаної: хрестики повернуті за напрямком."""
        seg = [0.0]
        for a, b in zip(pts, pts[1:], strict=False):
            seg.append(seg[-1] + math.hypot(b[0] - a[0], b[1] - a[1]))
        total = seg[-1]
        cols = int(total / s)
        rows = band.h
        lay = self.layers[layer]
        j = 0
        for i in range(cols):
            d = (i + 0.5) * total / cols
            while seg[j + 1] < d:
                j += 1
            a, b = pts[j], pts[j + 1]
            length = seg[j + 1] - seg[j]
            t = (d - seg[j]) / length
            x, y = a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t
            ang = math.atan2(b[1] - a[1], b[0] - a[0])
            nx, ny = -(b[1] - a[1]) / length, (b[0] - a[0]) / length
            for r in range(rows):
                k = band(r, i + BIG - cols // 2)
                if k is not None:
                    o = (r - (rows - 1) / 2) * s
                    lay.add_free_cross(x + nx * o, y + ny * o, s, ang, k)

    def flap(self, fill: Pattern, s=1.28):
        """Мотив і подвійний бордюр на кінці коміра (права половина - дзеркало)."""
        fs = min(s, 29.0 / max(fill.w, fill.h))
        self.field(
            fill, 186 - fill.w * fs / 2, 52.5 - fill.h * fs / 2, fill.w, fill.h, fs, layer="flap"
        )
        border = stack(
            (1, lambda r, c: 0),
            (1, lambda r, c: 1 if c % 2 == 0 else None),
            (1, lambda r, c: 0),
            (1, None),
            (2, lambda r, c: (0 if (c // 4) % 2 == 0 else 3) if r >= abs((c % 4) - 2) else None),
        )
        self.curve_band(border, G.FLAP_BORDER_SIDE, s)
        self.curve_band(border, G.FLAP_BORDER_BOTTOM, s)

    # ---------- гладь ----------
    def gilce(self, layer, x0, y0, length, scale=1.0, col="#ffffff", amp=5):
        """Полтавське «гільце»: плавна гілка з листям гладдю."""
        pts = [(x0 + math.sin(t / 22) * amp * scale, y0 + t) for t in range(0, int(length), 4)]
        d = G.polyline(pts)
        out = [
            f'<path d="{d}" stroke="{shade(col, -0.38)}" stroke-width="{2.8 * scale:.1f}" '
            f'fill="none" stroke-linecap="round"/><path d="{d}" stroke="{col}" '
            f'stroke-width="{1.8 * scale:.1f}" fill="none" stroke-linecap="round"/>'
        ]
        leaf_len = 11 * scale
        for i, (x, y) in enumerate(pts[2::3]):
            side = 1 if i % 2 else -1
            rot = side * 55 + (0 if side > 0 else 180)
            q = f"{leaf_len / 2:.1f}"
            out.append(
                f'<g transform="translate({x:.1f} {y:.1f}) rotate({rot})">'
                f'<path d="M0,0 Q{q},{-leaf_len / 3:.1f} {leaf_len:.1f},0 Q{q},{leaf_len / 3:.1f} 0,0Z" '
                f'fill="{shade(col, -0.34)}"/>'
                f'<path d="M.6,0 Q{q},{-leaf_len / 3.6:.1f} {leaf_len - 1:.1f},0 '
                f'Q{q},{leaf_len / 3.6:.1f} .6,0Z" fill="url(#{self.pid}gl)"/>'
                f'<path d="M1,0 L{leaf_len - 1.5:.1f},0" stroke="{shade(col, -0.3)}" stroke-width=".4"/></g>'
            )
            if i % 3 == 0:
                bx = x + side * 6 * scale
                out.append(
                    f'<circle cx="{bx:.1f}" cy="{y:.1f}" r="{2.2 * scale:.1f}" fill="{shade(col, -0.22)}"/>'
                    f'<circle cx="{bx - 0.3:.1f}" cy="{y - 0.3:.1f}" r="{1.7 * scale:.1f}" fill="{col}"/>'
                )
        self.layers[layer].raw.append("".join(out))

    def ornek(self, layer, x0, y0, length, cols, scale=1.0):
        """Кримськотатарський орьнек: лоза з тюльпанами й мигдалевим листям."""
        c1, c2, c3 = cols
        pts = [(x0 + math.sin(t / 26) * 9 * scale, y0 + t) for t in range(0, int(length), 4)]
        d = G.polyline(pts)
        out = [
            f'<path d="{d}" stroke="{shade(c2, -0.35)}" stroke-width="{2.4 * scale:.1f}" fill="none"/>'
            f'<path d="{d}" stroke="{c2}" stroke-width="{1.5 * scale:.1f}" fill="none"/>'
        ]
        for i, (x, y) in enumerate(pts[4::7]):
            side = 1 if i % 2 else -1
            if i % 2 == 0:
                out.append(
                    f'<g transform="translate({x + side * 10 * scale:.1f} {y:.1f}) rotate({side * 30}) '
                    f'scale({scale:.2f})">'
                    f'<path d="M0,4 C-6,2 -7,-6 -4,-10 C-2,-6 -1,-7 0,-11 C1,-7 2,-6 4,-10 C7,-6 6,2 0,4Z" '
                    f'fill="{shade(c1, -0.3)}"/>'
                    f'<path d="M0,3 C-5,1 -5.5,-5 -3.6,-8.5 C-2,-5 -1,-6 0,-9.5 C1,-6 2,-5 3.6,-8.5 '
                    f'C5.5,-5 5,1 0,3Z" fill="{c1}"/>'
                    f'<path d="M0,2 C-2,-1 -2,-5 0,-8" stroke="{shade(c1, 0.45)}" stroke-width=".8" fill="none"/>'
                    f'<path d="M0,4 L{-side * 7},8" stroke="{c2}" stroke-width="1.4"/></g>'
                )
            else:
                out.append(
                    f'<g transform="translate({x + side * 9 * scale:.1f} {y:.1f}) rotate({side * 70}) '
                    f'scale({scale:.2f})">'
                    f'<path d="M0,0 Q6,-5 13,0 Q6,5 0,0Z" fill="{shade(c2, -0.25)}"/>'
                    f'<path d="M1,0 Q6,-3.6 12,0 Q6,3.6 1,0Z" fill="{c2}"/>'
                    f'<circle cx="15" cy="0" r="3.2" fill="{shade(c3, -0.3)}"/>'
                    f'<circle cx="14.6" cy="-.4" r="2.5" fill="{c3}"/></g>'
                )
        self.layers[layer].raw.append("".join(out))
