"""Сторінка «Символи вишиванки»: тексти з data/symbols.json + схеми мотивів хрестиком."""

import json
from functools import cache
from pathlib import Path

from django.urls import reverse
from django.utils.safestring import mark_safe

from apps.patterns.models import Motif, Region

DATA_FILE = Path(__file__).resolve().parent.parent / "data" / "symbols.json"
THREAD = ["#B3261E", "#231C18"]


@cache
def data():
    return json.loads(DATA_FILE.read_text(encoding="utf-8"))


def stitch_svg(grid, palette=None, colors=None, label=""):
    """Схема мотиву: кожна клітинка - хрестик, один <path> на колір."""
    colors = colors or THREAD
    palette = palette or {"#": 0}
    rows, cols = len(grid), len(grid[0])
    by_color = {}
    for y, row in enumerate(grid):
        for x, ch in enumerate(row):
            if ch == ".":
                continue
            color = colors[palette.get(ch, 0) % len(colors)]
            by_color.setdefault(color, []).append(f"M{x + 0.15:g} {y + 0.15:g}l.7 .7m0-.7l-.7 .7")
    paths = "".join(f'<path stroke="{c}" d="{"".join(d)}"/>' for c, d in by_color.items())
    return mark_safe(
        f'<svg viewBox="-1 -1 {cols + 2} {rows + 2}" role="img" aria-label="{label}" '
        f'class="vd-sym__art"><g fill="none" stroke-width=".32" stroke-linecap="round">'
        f"{paths}</g></svg>"
    )


def _art(key, label, motifs):
    spec = data()["art"].get(key, {})
    if "grid" in spec:
        return stitch_svg(spec["grid"], colors=spec.get("colors"), label=label)
    motif = motifs.get(spec.get("motif"))
    geo = (motif.geometry_parameters or {}) if motif else {}
    if geo.get("format") != "pixel_grid_v1":
        return ""
    return stitch_svg(geo["grid"], geo["palette"], spec.get("colors"), label)


def _regions(slugs, by_slug):
    out = []
    for slug in slugs:
        region = by_slug.get(slug)
        if region:
            out.append(
                {
                    "name": region.short_name,
                    "url": reverse("patterns:region_detail", args=[slug]),
                }
            )
    return out


def build_page(lang):
    content = data()["en" if lang == "en" else "uk"]
    names = [spec["motif"] for spec in data()["art"].values() if "motif" in spec]
    motifs = {m.name_uk: m for m in Motif.objects.filter(name_uk__in=names)}
    by_slug = {r.slug: r for r in Region.objects.verified()}
    names_by_key = {}
    groups = []
    for group in content["groups"]:
        symbols = []
        for sym in group["symbols"]:
            names_by_key[sym["key"]] = sym["name"]
            symbols.append(
                {
                    **sym,
                    "art": _art(sym["key"], sym["name"], motifs),
                    "region_links": _regions(sym["regions"], by_slug),
                }
            )
        groups.append({**group, "symbols": symbols})
    rows = [
        {
            "symbol": names_by_key.get(key, key),
            "meaning": meaning,
            "who": who,
            "anchor": f"symbol-{key}",
            "region_links": _regions(_symbol_regions(content, key), by_slug),
        }
        for key, meaning, who in content["table_rows"]
    ]
    toc = [{"id": "what", "title": content["answer_title"]}]
    toc += [{"id": g["id"], "title": g["title"]} for g in groups]
    toc += [
        {"id": "ornek", "title": content["ornek_title"]},
        {"id": "names", "title": content["names_title"]},
        {"id": "new", "title": content["new_title"]},
        {"id": "table", "title": content["table_title"]},
        {"id": "why", "title": content["why_title"]},
        {"id": "faq", "title": content["faq_title"]},
        {"id": "sources", "title": content["sources_title"]},
    ]
    return {
        **content,
        "groups": groups,
        "table": rows,
        "toc": toc,
        "ornek_art": _art("ornek", content["ornek_title"], motifs),
        "ornek_region_links": _regions(content["ornek_regions"], by_slug),
        "terms": [
            {"name": s["name"], "description": " ".join(s["text"])}
            for g in content["groups"]
            for s in g["symbols"]
        ],
    }


def _symbol_regions(content, key):
    for group in content["groups"]:
        for sym in group["symbols"]:
            if sym["key"] == key:
                return sym["regions"]
    return []


def page_markdown(lang):
    """Текст сторінки для llms-full.txt."""
    c = data()["en" if lang == "en" else "uk"]
    out = [c["lead"], "", f"### {c['answer_title']}", *c["answer"]]
    for group in c["groups"]:
        out += ["", f"### {group['title']}", group["intro"]]
        for sym in group["symbols"]:
            out += ["", f"**{sym['name']}**", *sym["text"]]
    out += ["", f"### {c['ornek_title']}", *c["ornek"]]
    out += [f"- {a}: {b}" for a, b in c["ornek_rows"]]
    out += ["", f"### {c['names_title']}", *c["names"], "", f"### {c['new_title']}", *c["new"]]
    out += ["", f"### {c['why_title']}", *c["why"], "", f"### {c['faq_title']}"]
    for q, a in c["faq"]:
        out += [f"**{q}**", a]
    return "\n\n".join(p for p in out if p is not None)
