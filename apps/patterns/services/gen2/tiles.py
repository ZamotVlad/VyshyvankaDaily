"""Окремі плитки мотивів (сторінки регіонів, «Символи», мапа) тим самим хрестиком, що й сорочки."""

from html import escape

from .grid import Pattern
from .shirt import Shirt
from .stitches import Layer, StitchWriter


def _wrap(pid: str, w: float, h: float, label: str, defs: str, body: str, css: str) -> str:
    cls = f' class="{css}"' if css else ""
    return (
        f'<svg viewBox="-1 -1 {w + 2:g} {h + 2:g}" xmlns="http://www.w3.org/2000/svg" role="img" '
        f'aria-label="{escape(label)}"{cls}><defs>{defs}</defs>'
        f'<g filter="url(#{pid}em)">{body}</g></svg>'
    )


def _shadow(pid: str) -> str:
    return (
        f'<filter id="{pid}em"><feDropShadow dx=".12" dy=".18" stdDeviation=".12" '
        f'flood-color="#2a1d12" flood-opacity=".45"/></filter>'
    )


def stitch_tile(
    pattern: Pattern,
    palette: list[str],
    label: str,
    pid: str,
    w: int | None = None,
    h: int | None = None,
    tech: str = "x",
    css: str = "",
) -> str:
    """Мотив хрестиком (або гладдю) у власних координатах: 1 клітинка = 1 одиниця."""
    w = w or pattern.w
    h = h or pattern.h
    layer = Layer()
    key = (1.0, 0.0, 0.0)
    for r in range(h):
        c = 0
        while c < w:
            k = pattern(r, c)
            if k is None:
                c += 1
                continue
            if tech == "satin":
                n = 1
                while c + n < w and n < 6 and pattern(r, c + n) == k:
                    n += 1
                layer.add_satin(key, c, r, n, k)
                c += n
            else:
                layer.add_cross(key, c, r, k)
                c += 1
    writer = StitchWriter(pid, palette)
    body = writer.layer(layer)
    return _wrap(pid, w, h, label, _shadow(pid) + "".join(writer.defs), body, css)


def smooth_tile(kind: str, palette: list[str], label: str, pid: str, css: str = "") -> str:
    """Гладь: «гільце» (Полтавщина), орьнек (Крим) або гуцульські «кучерики»."""
    sh = Shirt(palette, "#ffffff", pid=pid)
    writer = StitchWriter(pid, palette)
    if kind == "gilce":
        sh.gilce("body", 20, 2, 64, 1.0, "#ffffff")
        w, h = 40, 64
    elif kind == "ornek":
        sh.ornek("body", 20, -4, 72, tuple(palette[:3]), 0.9)
        w, h = 40, 64
    else:
        step = 3.2
        for i in range(9):
            for j in range(10):
                x = 2 + j * step + (step / 2 if i % 2 else 0)
                sh.layers["body"].add_knot(x, 2 + i * step * 0.9, step * 0.48, (j + i // 2) % 3)
        w, h = 36, 28
    body = writer.layer(sh.layers["body"])
    defs = (
        f'<pattern id="{pid}gl" width="1.3" height="1.3" patternUnits="userSpaceOnUse" '
        f'patternTransform="rotate(35)"><rect width="1.3" height="1.3" fill="#fff"/>'
        f'<rect width=".45" height="1.3" fill="#e4dfd6"/></pattern>'
    )
    return _wrap(pid, w, h, label, _shadow(pid) + defs + writer.knot_defs(), body, css)
