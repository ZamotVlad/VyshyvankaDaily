"""Мапа регіонів на /regions/: контури областей + мотив і кольори кожного регіону."""

import json
import re
from functools import cache
from pathlib import Path

from django.urls import reverse
from django.utils.html import strip_tags
from django.utils.safestring import mark_safe

from apps.patterns.region_groups import GROUPS

DATA_FILE = Path(__file__).resolve().parent.parent / "data" / "region_map.json"
CELL = 3
CITIES = ("m-kyiv", "m-sevastopol")
WHITE = "#FFFFFF"
# Зсув підписів там, де сусідні назви накладаються.
LABEL_NUDGE = {"cherkaska-oblast": (-22, 10), "ternopilska-oblast": (-10, 10)}


@cache
def geometry():
    return json.loads(DATA_FILE.read_text(encoding="utf-8"))


def _group_of():
    return {slug: (key, label) for key, label, slugs in GROUPS for slug in slugs}


def _grid(motif):
    geo = motif.geometry_parameters or {}
    if geo.get("format") != "pixel_grid_v1":
        return None
    return geo


def pick_motif(region):
    """Мотив із найбільшою кількістю стібків - на дрібній мапі він читається найкраще."""
    best, best_cells = None, -1
    for motif in region.compatible_motifs.all():
        geo = _grid(motif)
        if not geo:
            continue
        cells = sum(ch != "." for row in geo["grid"] for ch in row)
        if cells > best_cells:
            best, best_cells = motif, cells
    return best


def motif_pattern(slug, motif, colors):
    """SVG <pattern> з хрестиків: один <path> на колір."""
    geo = _grid(motif) if motif else None
    if not geo or not colors:
        return ""
    grid, palette = geo["grid"], geo["palette"]
    by_color = {}
    for y, row in enumerate(grid):
        for x, ch in enumerate(row):
            if ch == ".":
                continue
            color = colors[palette[ch] % len(colors)]
            if color.upper() == WHITE:
                color = "#FFFDF8"
            x0, y0 = x * CELL + 0.45, y * CELL + 0.45
            by_color.setdefault(color, []).append(f"M{x0:g} {y0:g}l2.1 2.1m0-2.1l-2.1 2.1")
    w = (len(grid[0]) + 3) * CELL
    h = (len(grid) + 3) * CELL
    shift = sum(map(ord, slug))
    paths = "".join(f'<path stroke="{c}" d="{"".join(d)}"/>' for c, d in by_color.items())
    return (
        f'<pattern id="vd-m-{slug}" width="{w}" height="{h}" patternUnits="userSpaceOnUse" '
        f'patternTransform="translate({shift % 7 * 2} {shift % 5 * 2})">'
        f'<g fill="none" stroke-width="1.05" stroke-linecap="round">{paths}</g></pattern>'
    )


def _label_y(slug, cy, today_slug):
    if slug in CITIES:
        return cy - 18
    return cy + LABEL_NUDGE.get(slug, (0, 0))[1]


def _is_light(colors):
    """Білі чи світло-сірі нитки кладемо на небілене полотно, інакше їх не видно."""
    if not colors:
        return False
    for c in colors:
        r, g, b = (int(c.lstrip("#")[i : i + 2], 16) for i in (0, 2, 4))
        if (r + g + b) / 3 > 170:
            return True
    return False


def _teaser(region):
    text = strip_tags(region.symbolism_description or "").strip()
    match = re.match(r"(.+?[.!?])(\s|$)", text)
    return (match.group(1) if match else text)[:240]


def build_region_map(regions, today_slug=None):
    geo = geometry()
    groups = _group_of()
    items = []
    for region in regions:
        shape = geo["regions"].get(region.slug)
        if not shape:
            continue
        colors = region.shown_colors
        motif = pick_motif(region)
        key, label = groups.get(region.slug, ("", ""))
        items.append(
            {
                "slug": region.slug,
                "url": reverse("patterns:region_detail", args=[region.slug]),
                "name": region.name,
                "short_name": region.short_name,
                "group": key,
                "group_label": label,
                "colors": colors,
                "colors_attr": " ".join(colors),
                "motif": motif.name.split(" (")[0] if motif else "",
                "teaser": _teaser(region),
                "pattern": mark_safe(motif_pattern(region.slug, motif, colors)),
                "d": shape["d"],
                # Рядками: локалізація шаблону інакше ставить кому замість крапки.
                "cx": f"{shape['cx']:g}",
                "cy": f"{shape['cy']:g}",
                "label_x": f"{shape['cx'] + LABEL_NUDGE.get(region.slug, (0, 0))[0]:g}",
                "label_y": f"{_label_y(region.slug, shape['cy'], today_slug):g}",
                "sort_x": shape["cx"],
                "small": region.slug in CITIES,
                "raw": _is_light(colors),
                "today": region.slug == today_slug,
            }
        )
    items.sort(key=lambda i: (i["small"], i["sort_x"]))
    for index, item in enumerate(items):
        item["index"] = index
    present = {i["group"] for i in items}
    groups = [(key, label) for key, label, _slugs in GROUPS if key in present]
    return {"width": geo["width"], "height": geo["height"], "items": items, "groups": groups}
