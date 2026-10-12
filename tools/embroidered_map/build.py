"""Вишита карта України: уся мапа - канва хрестиком, кожен регіон - власна композиція.

    pip install numpy fonttools brotli   # Pillow і Django вже в requirements
    python tools/embroidered_map/build.py --lang uk --width 1200 --out karta.png

Контури - apps/patterns/data/region_map.json, назви - з бази (Region.short_name).
"""

import argparse
import json
import os
import random
import re
import sys
from pathlib import Path

import numpy as np
from fontTools.ttLib import TTFont
from fontTools.varLib.instancer import instantiateVariableFont
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from motifs import cells as main_cells  # noqa: E402

geo = json.loads((ROOT / "apps/patterns/data/region_map.json").read_text(encoding="utf-8"))
W, H = geo["width"], geo["height"]
GW = 400
GH = round(GW * H / W)
PAD = 14
PX = 8
random.seed(7)


def grid(s):
    rows = [r for r in s.strip("\n").split("\n")]
    w = max(len(r) for r in rows)
    return (
        {
            (x, y): "abcd".index(ch)
            for y, r in enumerate(rows)
            for x, ch in enumerate(r)
            if ch in "abcd"
        },
        w,
        len(rows),
    )


FILL = {
    "cross": grid(".a.\naba\n.a."),
    "dots": grid("a.a\n.b.\na.a"),
    "rhomb": grid("..a..\n.a.a.\na.b.a\n.a.a.\n..a.."),
    "star": grid("a...a\n.a.a.\n..b..\n.a.a.\na...a"),
    "flower": grid(".a.a.\naabaa\n.aba.\naabaa\n.a.a."),
    "sprig": grid("..a..\n.aaa.\n..b..\n.b.b.\n..b.."),
    "hook": grid("aa...\na....\na.a.a\n....a\n...aa"),
    "berry": grid(".aa.\naaaa\n.aa.\n..b."),
    "tiny": grid("a"),
}
BAND = {
    "zig": grid("a...a...\n.a.a.a.a\n..a...a."),
    "wave": grid("..aa....aa..\n.a..a..a..a.\na....aa....a"),
    "teeth": grid("aaaaaaaa\n.a.a.a.a"),
    "chain": grid(".a..a..a.\na.a.a.a.a\n.a..a..a."),
    "line": grid("aaaa"),
    "rhombs": grid("..a.....a...\n.aba...aba..\naabaa.aabaa.\n.aba...aba..\n..a.....a..."),
}

R, K, B, G, MR, OR, GR = "#B5241C", "#2A1F1A", "#2D418A", "#C99A2E", "#7A1A22", "#B5601E", "#4E7F57"
# регіон: (палітра, полотно, заповнювач, композиція, смуга)
STYLE = {
    "volynska-oblast": ([R, K, B], "#EDE4D3", "dots", "halfdrop", None),
    "rivnenska-oblast": (["#C02A20", B, K], "#E6DBC6", "cross", "diag", None),
    "zhytomyrska-oblast": (["#A9261C", K, B], "#EAE0CD", "rhomb", "bands", "chain"),
    "kyivska-oblast": ([R, K, "#3D6B36"], "#F0E8D9", "sprig", "halfdrop", None),
    "m-kyiv": ([K, R], "#F2EADD", "tiny", "grid", None),
    "chernihivska-oblast": (["#C13A2C", "#4A3A30"], "#F3ECE0", "dots", "grid", None),
    "sumska-oblast": ([R, B, G], "#ECE2CF", "flower", "bands", "wave"),
    "poltavska-oblast": (["WHITE", "WHITE"], "#B9AB90", "star", "halfdrop", None),
    "kharkivska-oblast": ([K, R], "#E3D6BD", "sprig", "bands", "teeth"),
    "luhanska-oblast": (["#C3302A", "#4F9CC0"], "#EFE6D6", "berry", "diag", None),
    "donetska-oblast": (["#C42A1F", K], "#E8DCC6", "hook", "halfdrop", None),
    "dnipropetrovska-oblast": (["#A01E18", K], "#EDE4D3", "rhomb", "bands", "zig"),
    "khersonska-oblast": ([K, "#5A4A3E"], "#E6DBC8", "cross", "halfdrop", None),
    "mykolaivska-oblast": ([R, K, "#6F808C"], "#E8E0D1", "dots", "bands", "wave"),
    "odeska-oblast": ([K, R, G], "#EAE0CB", "star", "diag", None),
    "kirovohradska-oblast": ([K, R, "#5F7D2A"], "#EFE6D5", "berry", "halfdrop", None),
    "cherkaska-oblast": ([R, K, G], "#E7DDC9", "hook", "grid", None),
    "vinnytska-oblast": ([K, MR], "#F1E9DA", "rhomb", "bands", "teeth"),
    "khmelnytska-oblast": ([K, B], "#ECE3D2", "tiny", "bands", "zig"),
    "ternopilska-oblast": ([K, "#C4271D"], "#E2D6BF", "flower", "halfdrop", None),
    "lvivska-oblast": ([K, R, G], "#F4EEE3", "cross", "grid", None),
    "ivano-frankivska-oblast": ([OR, MR, G], "#E6D8BF", "hook", "bands", "rhombs"),
    "chernivetska-oblast": ([MR, K, "#B9AE3A", "#5F7D2A"], "#E8DCC5", "berry", "halfdrop", None),
    "zakarpatska-oblast": ([MR, K, G, "#3D6B36"], "#E4D7BF", "sprig", "bands", "chain"),
    "zaporizka-oblast": ([R, K], "#EEE3CF", "star", "diag", None),
    "ar-krym": (["#B54A63", "#4E7F57", "#C9963E"], "#F1E7D6", "flower", "halfdrop", None),
    "m-sevastopol": (["#B54A63", "#4E7F57", "#C9963E"], "#F3EADC", "tiny", "grid", None),
}


def stamp(tile, cells_, w, h, ox, oy, cmap=None):
    TH, TW = tile.shape
    for (x, y), c in cells_.items():
        tile[(oy + y) % TH, (ox + x) % TW] = c if cmap is None else cmap.get(c, c)


def swap_map(n):
    return {0: 1 % max(n, 1), 1: 0} if n > 1 else {0: 0, 1: 0}


SMALL_FILL = {"cross": FILL["cross"], "dots": FILL["dots"], "tiny": FILL["tiny"]}


def corner_fill(tile, fc, fw, fh, px, py, mw, mh, cmap):
    TH, TW = tile.shape
    for cy in range(0, TH, py):
        for cx in range(0, TW, px):
            stamp(
                tile,
                fc,
                fw,
                fh,
                cx + mw + (px - mw) // 2 - fw // 2,
                cy + mh + (py - mh) // 2 - fh // 2,
                cmap,
            )


def build_tile(slug):
    mc, mw, mh = main_cells(slug)
    pal, _, fill, comp, band = STYLE[slug]
    n = len(pal)
    fc, fw, fh = FILL[fill] if fill in SMALL_FILL else FILL["cross"]
    sw = swap_map(n)
    third = {0: 2 % n, 1: 0} if n > 2 else sw
    g = 3
    px, py = mw + g, mh + g
    if comp == "halfdrop":
        tile = -np.ones((py * 2, px * 2), int)
        stamp(tile, mc, mw, mh, 0, 0)
        stamp(tile, mc, mw, mh, px, py)
        stamp(tile, mc, mw, mh, px, 0, sw)
        stamp(tile, mc, mw, mh, 0, py, sw)
        corner_fill(tile, fc, fw, fh, px, py, mw, mh, third)
    elif comp == "grid":
        tile = -np.ones((py * 2, px * 2), int)
        stamp(tile, mc, mw, mh, 0, 0)
        stamp(tile, mc, mw, mh, px, 0)
        stamp(tile, mc, mw, mh, px // 2, py, sw)
        stamp(tile, mc, mw, mh, px // 2 + px, py, sw)
        corner_fill(tile, fc, fw, fh, px, py, mw, mh, third)
    elif comp == "diag":
        s = max(mw, mh) + 2
        tile = -np.ones((2 * s, 2 * s), int)
        for k in range(2 * s):
            tile[k, k] = 1 if n > 1 else 0
            tile[k, 2 * s - 1 - k] = 1 if n > 1 else 0
        stamp(tile, mc, mw, mh, s - mw // 2, -(mh // 2))
        stamp(tile, mc, mw, mh, -(mw // 2), s - mh // 2, sw)
        stamp(tile, fc, fw, fh, s - fw // 2, s - fh // 2, third)
        stamp(tile, fc, fw, fh, -(fw // 2), -(fh // 2), third)
    else:  # bands: смуга + ряд мотивів у двох гамах
        bc, bw, bh = BAND[band]
        tw = (mw + 2) * 2
        tw = ((tw + bw - 1) // bw) * bw
        th = mh + bh + 4
        tile = -np.ones((th, tw), int)
        stamp(tile, mc, mw, mh, 0, bh + 2)
        stamp(tile, mc, mw, mh, tw // 2, bh + 2, sw)
        for x0 in range(0, tw, bw):
            stamp(tile, bc, bw, bh, x0, 1, {0: 1 if n > 1 else 0, 1: 2 % n if n > 2 else 0})
    # ґрунт: рідкі стібки там, де навколо порожньо
    TH, TW = tile.shape
    for y in range(0, TH, 4):
        for x in range(0, TW, 4):
            ok = all(
                tile[(y + dy) % TH, (x + dx) % TW] < 0
                for dy in (-2, -1, 0, 1, 2)
                for dx in (-2, -1, 0, 1, 2)
            )
            if ok:
                tile[y, x] = 2 % n if n > 2 else (1 if n > 1 else 0)
    return tile


def polys(d):
    out = []
    for sub in re.findall(r"M[^M]*", d):
        nums = [float(n) for n in re.findall(r"-?\d+\.?\d*", sub)]
        x, y = nums[0], nums[1]
        pts = [(x, y)]
        for i in range(2, len(nums) - 1, 2):
            x += nums[i]
            y += nums[i + 1]
            pts.append((x, y))
        out.append(pts)
    return out


def render_base():
    slugs = list(geo["regions"])
    order = sorted(slugs, key=lambda s: s in ("m-kyiv", "m-sevastopol"))
    lab = Image.new("I", (GW, GH), 0)
    dr = ImageDraw.Draw(lab)
    sc = GW / W
    for idx, s in enumerate(order, start=1):
        for pts in polys(geo["regions"][s]["d"]):
            dr.polygon([(x * sc, y * sc) for x, y in pts], fill=slugs.index(s) + 1)
    L = np.array(lab)

    border = np.zeros_like(L, bool)
    for dy, dx in ((0, 1), (1, 0)):
        a, b = L[: GH - dy, : GW - dx], L[dy:, dx:]
        diff = (a != b) & (a > 0) & (b > 0)
        border[: GH - dy, : GW - dx] |= diff

    tiles = {s: build_tile(s) for s in slugs}
    offs = {s: (random.randrange(40), random.randrange(40)) for s in slugs}

    CW, CH = GW + 2 * PAD, GH + 2 * PAD
    img = Image.new("RGB", (CW * PX, CH * PX), "#120E0C")
    # фон: легкий віньєт
    bg = np.zeros((CH * PX, CW * PX, 3), np.float32)
    yy, xx = np.mgrid[0 : CH * PX, 0 : CW * PX]
    r = np.hypot((xx - CW * PX / 2) / (CW * PX), (yy - CH * PX * 0.45) / (CH * PX))
    v = np.clip(1 - r * 1.3, 0, 1)[..., None]
    bg = (np.array([14, 11, 9]) + v * np.array([24, 19, 15])).astype(np.uint8)
    img = Image.fromarray(bg)

    # полотно
    linen = np.zeros((CH, CW, 3), np.uint8)
    mask = np.zeros((CH, CW), bool)
    for s in slugs:
        m = L == slugs.index(s) + 1
        col = tuple(int(STYLE[s][1][i : i + 2], 16) for i in (1, 3, 5))
        linen[PAD : PAD + GH, PAD : PAD + GW][m] = col
        mask[PAD : PAD + GH, PAD : PAD + GW] |= m
    lin = Image.fromarray(linen).resize((CW * PX, CH * PX), Image.NEAREST)
    noise = (np.random.default_rng(3).normal(0, 1, (CH * PX, CW * PX)) * 7).astype(np.int16)
    weave = ((np.arange(CW * PX) % 4 == 0)[None, :] | (np.arange(CH * PX) % 4 == 0)[:, None]) * -9
    la = np.array(lin).astype(np.int16) + noise[..., None] + weave[..., None]
    lin = Image.fromarray(np.clip(la, 0, 255).astype(np.uint8))
    M = Image.fromarray((np.kron(mask, np.ones((PX, PX))) * 255).astype(np.uint8))
    # тінь під полотном
    shadow = M.filter(ImageFilter.GaussianBlur(18)).point(lambda p: p * 0.8)
    img.paste(Image.new("RGB", img.size, "#000"), (0, 9), shadow)
    img.paste(lin, (0, 0), M)

    draw = ImageDraw.Draw(img)

    def hexrgb(h):
        return tuple(int(h[i : i + 2], 16) for i in (1, 3, 5))

    def jitter(rgb, k):
        return tuple(max(0, min(255, int(c * k))) for c in rgb)

    rng = random.Random(11)
    WHITE = (252, 250, 244)
    for gy in range(GH):
        for gx in range(GW):
            li = L[gy, gx]
            if not li:
                continue
            s = slugs[li - 1]
            if border[gy, gx]:
                rgb = hexrgb("#1E1612")
            else:
                t = tiles[s]
                ox, oy = offs[s]
                c = t[(gy + oy) % t.shape[0], (gx + ox) % t.shape[1]]
                if c < 0:
                    continue
                pal = STYLE[s][0]
                col = pal[c % len(pal)]
                rgb = WHITE if col == "WHITE" else hexrgb(col)
            k = rng.uniform(0.9, 1.08)
            base = jitter(rgb, k)
            dark = jitter(rgb, k * (0.5 if rgb != WHITE else 0.62))
            hi = jitter(rgb, min(1.35, k * 1.28)) if rgb != WHITE else (255, 255, 255)
            x0, y0 = (gx + PAD) * PX, (gy + PAD) * PX
            p = 1.2
            a, b2 = (x0 + p, y0 + p), (x0 + PX - p, y0 + PX - p)
            c1, c2 = (x0 + PX - p, y0 + p), (x0 + p, y0 + PX - p)
            draw.line([a, b2], fill=dark, width=4)
            draw.line([(a[0] - 0.5, a[1] - 0.5), (b2[0] - 0.5, b2[1] - 0.5)], fill=base, width=3)
            draw.line([c1, c2], fill=dark, width=4)
            draw.line([(c1[0] - 0.5, c1[1] - 0.5), (c2[0] - 0.5, c2[1] - 0.5)], fill=base, width=3)
            draw.line(
                [(c1[0] - 1.6, c1[1] + 0.6), (x0 + PX / 2, y0 + PX / 2 - 0.9)], fill=hi, width=1
            )

    return img


def region_names(lang):
    sys.path.insert(0, str(ROOT))
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")
    import django

    django.setup()
    from django.utils import translation

    from apps.patterns.models import Region

    translation.activate(lang)
    return {r.slug: r.short_name for r in Region.objects.all()}


NUDGE = {
    "cherkaska-oblast": (-18, 8),
    "ternopilska-oblast": (-8, 8),
    "ivano-frankivska-oblast": (6, -10),
    "zakarpatska-oblast": (16, 12),
    "m-kyiv": (0, -18),
    "m-sevastopol": (0, 18),
    "kyivska-oblast": (-12, 30),
}


def add_labels(base, lang, outw, font_path):
    names = region_names(lang)
    k = outw / base.width
    img = base.resize((outw, round(base.height * k)), Image.LANCZOS).convert("RGBA")
    s = outw / 1200
    font = ImageFont.truetype(font_path, round(12.5 * s))
    sc = GW / W

    def to_px(x, y):
        return (PAD + x * sc) * PX * k, (PAD + y * sc) * PX * k

    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    shadow = Image.new("RGBA", img.size, (0, 0, 0, 0))
    dl, ds = ImageDraw.Draw(layer), ImageDraw.Draw(shadow)
    for slug, info in geo["regions"].items():
        dx, dy = NUDGE.get(slug, (0, 0))
        x, y = to_px(float(info["cx"]) + dx, float(info["cy"]) + dy)
        t = names[slug]
        w, h = dl.textlength(t, font=font) + 26 * s, 24 * s
        box = (x - w / 2, y - h / 2, x + w / 2, y + h / 2)
        ds.rounded_rectangle(
            (box[0], box[1] + 2 * s, box[2], box[3] + 2 * s), radius=h / 2, fill=(0, 0, 0, 150)
        )
        dl.rounded_rectangle(
            box,
            radius=h / 2,
            fill=(23, 18, 15, 238),
            outline=(255, 248, 238, 60),
            width=max(1, round(s)),
        )
        dl.text((x, y + 0.5 * s), t, font=font, fill=(255, 248, 238), anchor="mm")
        if slug in ("m-kyiv", "m-sevastopol"):
            px, py = to_px(float(info["cx"]), float(info["cy"]))
            r = 4 * s
            dl.ellipse(
                (px - r, py - r, px + r, py + r),
                fill=(184, 35, 27),
                outline=(255, 248, 238),
                width=max(1, round(1.4 * s)),
            )
    img = Image.alpha_composite(img, shadow.filter(ImageFilter.GaussianBlur(3 * s)))
    return Image.alpha_composite(img, layer).convert("RGB")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lang", default="uk")
    ap.add_argument("--width", type=int, default=1200)
    ap.add_argument("--out", default="karta.png")
    ap.add_argument("--no-labels", action="store_true")
    a = ap.parse_args()
    base = render_base()
    if a.no_labels:
        base.save(a.out)
        return
    font = instantiateVariableFont(TTFont(ROOT / "static/fonts/unbounded.woff2"), {"wght": 700})
    font.flavor = None
    font_path = Path(a.out).with_suffix(".font.ttf")
    font.save(font_path)
    try:
        add_labels(base, a.lang, a.width, str(font_path)).save(a.out)
    finally:
        font_path.unlink()


if __name__ == "__main__":
    main()
