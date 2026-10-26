"""Візерунки в клітинках: мотиви, бордюри й їх комбінування.

Візерунок - функція (рядок, стовпець) -> роль кольору або None.
Ролі: 0 основний, 1 темний (контур), 2 акцент, 3 акцент-2, 4 листя, далі - додаткові.
"""

import math
from collections.abc import Callable

Cell = Callable[[int, int], int | None]

# Зсув, щоб індекс стовпця завжди був додатним для % і //
BIG = 10080 * 11 * 13 * 17 * 19 * 23 * 29 * 31


class Pattern:
    """Візерунок із розміром (w, h); h=0 - безкінечний по вертикалі."""

    __slots__ = ("fn", "w", "h")

    def __init__(self, fn: Cell, w: int = 0, h: int = 0):
        self.fn, self.w, self.h = fn, w, h

    def __call__(self, r: int, c: int) -> int | None:
        return self.fn(r, c)

    def recolor(self, mapping: dict[int, int]) -> "Pattern":
        fn = self.fn

        def cell(r, c):
            k = fn(r, c)
            return None if k is None else mapping.get(k, k)

        return Pattern(cell, self.w, self.h)


class Canvas:
    """Полотно для побудови мотиву клітинками."""

    def __init__(self, w: int, h: int):
        self.w, self.h, self.g = w, h, {}

    def put(self, r, c, k, over=True):
        r, c = int(round(r)), int(round(c))
        if 0 <= r < self.h and 0 <= c < self.w and (over or (r, c) not in self.g):
            self.g[(r, c)] = k

    def disk(self, cy, cx, rad, k, over=True):
        for r in range(int(cy - rad - 1), int(cy + rad + 2)):
            for c in range(int(cx - rad - 1), int(cx + rad + 2)):
                if (r - cy) ** 2 + (c - cx) ** 2 <= rad * rad + 0.35:
                    self.put(r, c, k, over)

    def rhomb(self, cy, cx, rad, k, hollow=0, over=True):
        for r in range(int(cy - rad), int(cy + rad + 1)):
            for c in range(int(cx - rad), int(cx + rad + 1)):
                d = abs(r - cy) + abs(c - cx)
                if d <= rad and (not hollow or d > rad - hollow):
                    self.put(r, c, k, over)

    def line(self, r0, c0, r1, c1, k, over=True):
        n = int(max(abs(r1 - r0), abs(c1 - c0))) or 1
        for i in range(n + 1):
            self.put(r0 + (r1 - r0) * i / n, c0 + (c1 - c0) * i / n, k, over)

    def petal(self, cy, cx, dy, dx, a, b, wmax, k, over=True):
        diag = dy and dx
        for t in range(a, b + 1):
            w = int(round(wmax * math.sin(math.pi * (t - a + 0.5) / (b - a + 1))))
            br, bc = cy + dy * t, cx + dx * t
            for j in range(-w, w + 1):
                if diag:
                    self.put(br + j, bc + j * (-dy * dx), k, over)
                    self.put(br + j, bc + j * (-dy * dx) + dx, k, over)
                elif dy:
                    self.put(br, bc + j, k, over)
                else:
                    self.put(br + j, bc, k, over)

    def leaf(self, cy, cx, dy, dx, length=7, w=2.0, k=3, vein=4):
        """Видовжений гострий листок із жилкою."""
        n = math.hypot(dy, dx)
        uy, ux = dy / n, dx / n
        for i in range(int(length * 4) + 1):
            t = i / 4
            ww = w * math.sin(math.pi * t / length) ** 0.8
            by, bx = cy + uy * t, cx + ux * t
            steps = int(ww * 4)
            for j in range(-steps, steps + 1):
                o = j / 4
                self.put(by - ux * o, bx + uy * o, k, over=False)
        for i in range(int(length * 2)):
            t = i / 2
            self.put(cy + uy * t, cx + ux * t, vein)

    def outline(self, k):
        add = []
        for r, c in list(self.g):
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                q = (r + dr, c + dc)
                if q not in self.g and 0 <= q[0] < self.h and 0 <= q[1] < self.w:
                    add.append(q)
        for q in add:
            self.g[q] = k
        return self

    def stamp(self, p: Pattern, r0, c0, mirror=False):
        for r in range(p.h):
            for c in range(p.w):
                k = p(r, c)
                if k is not None:
                    self.put(r0 + r, c0 + (p.w - 1 - c if mirror else c), k)

    def pattern(self) -> Pattern:
        g = dict(self.g)
        return Pattern(lambda r, c: g.get((r, c)), self.w, self.h)


def from_rows(rows: list[str], mapping: dict[str, int]) -> Pattern:
    w = max(len(r) for r in rows)
    rows = [r.ljust(w, ".") for r in rows]

    def cell(r, c):
        if 0 <= r < len(rows) and 0 <= c < w:
            return mapping.get(rows[r][c])
        return None

    return Pattern(cell, w, len(rows))


# ---------- бордюри (h рядків, безкінечні по горизонталі) ----------


def b_line(k) -> Cell:
    return lambda r, c: k


def b_dots(k, p=2) -> Cell:
    return lambda r, c: k if c % p == 0 else None


def b_teeth(h, k, flip=False) -> Cell:
    return lambda r, c: k if ((h - 1 - r) if flip else r) >= abs((c % (2 * h)) - h) else None


def b_kryv(h, k, p=8) -> Cell:
    return lambda r, c: k if r == round(abs((c % p) - p / 2) * (h - 1) / (p / 2)) else None


def b_chain(k1, k2, h=5) -> Cell:
    rad = h // 2

    def cell(r, c):
        if c % (h + 1) >= h:
            return None
        d = abs(r - rad) + abs(c % (h + 1) - rad)
        return k1 if d == rad else (k2 if d == 0 else None)

    return cell


def b_wave(k, h=5, p=10) -> Cell:
    def cell(r, c):
        y = (math.sin(c * 2 * math.pi / p) + 1) / 2 * (h - 1)
        return k if abs(r - y) < 0.6 else None

    return cell


def b_rams(k1, k2) -> Cell:
    """«Баранячі ріжки»."""
    horn = {(0, 2), (0, 3), (0, 4), (1, 5), (2, 5), (2, 4), (3, 3), (4, 3), (5, 2), (6, 1), (6, 0)}

    def cell(r, c):
        x = c % 8
        if (r, x) in horn:
            return k1
        return k2 if (r, x) in ((3, 6), (3, 7)) else None

    return cell


MEANDER = ("#######.", "......#.", ".####.#.", ".#..#.#.", ".#.##.#.", ".#....#.", ".######.")


def b_meander(k) -> Cell:
    return lambda r, c: k if 0 <= r < 7 and MEANDER[r][c % 8] == "#" else None


def b_repeat(m: Pattern, gap=1) -> Cell:
    """Мотив, повторений уздовж бордюру."""
    pc = m.w + gap

    def cell(r, c):
        x = (c + m.w // 2) % pc
        return m(r, x) if x < m.w else None

    return cell


def stack(*specs: tuple[int, Cell | None]) -> Pattern:
    """Бордюри один під одним: (кількість рядків, візерунок)."""

    def cell(r, c):
        y = 0
        for n, fn in specs:
            if r < y + n:
                return fn(r - y, c) if fn else None
            y += n
        return None

    return Pattern(cell, 0, sum(n for n, _ in specs))


def column(m: Pattern, gap=0, side=None, k=1) -> Pattern:
    """Колона мотивів із бічними лініями (side: роль, "dots" або None)."""
    p, w = m.h + gap, m.w + 4

    def cell(r, c):
        if side is not None and c in (0, w - 1):
            if side == "dots":
                return k if r % 2 == 0 else None
            return side
        y = r % p
        if 2 <= c < w - 2 and y < m.h:
            return m(y, c - 2)
        return None

    return Pattern(cell, w)


def vband(fn: Cell, w: int) -> Pattern:
    return Pattern(fn, w)
