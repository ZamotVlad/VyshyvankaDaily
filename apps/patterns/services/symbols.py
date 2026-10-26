"""Сторінка «Символи вишиванки»: тексти з data/symbols.json + схеми мотивів хрестиком."""

import json
from datetime import date
from functools import cache
from pathlib import Path

from django.urls import reverse
from django.utils.html import strip_tags
from django.utils.safestring import mark_safe

from apps.patterns.models import Region
from apps.patterns.services.gen2 import motifs as M
from apps.patterns.services.gen2 import regional as R
from apps.patterns.services.gen2.grid import Pattern, from_rows
from apps.patterns.services.gen2.tiles import smooth_tile, stitch_tile

DATA_FILE = Path(__file__).resolve().parent.parent / "data" / "symbols.json"
THREAD = ["#B3261E", "#231C18", "#C9A227", "#2E6B3A", "#1E5128", "#7D0F18", "#D9444C"]


@cache
def data():
    return json.loads(DATA_FILE.read_text(encoding="utf-8"))


# символ -> мотив генератора 2.0 (той самий хрестик, що й на сорочках)
SYMBOL_MOTIFS = {
    "romb": lambda: M.rich(10, "rhomb"),
    "zirka": lambda: M.star(10),
    "sontse": lambda: M.sun(10),
    "kryvulka": lambda: Pattern(R.kryv_rows((0, 1)), 24, 24),
    "derevo": lambda: M.tree(25, 39, pot=False),
    "vazon": M.lily,
    "ruzha": M.rose_branch,
    "kalyna": M.kalyna,
    "vynohrad": M.grapes,
    "sosonka": lambda: M.sosonka(24),
    "ptakh": M.bird,
    "orel": M.orlyk,
    "svitove": M.birds_tree,
}


def _art(key, label, css="vd-sym__art", prefix="s"):
    spec = data()["art"].get(key, {})
    pid = f"{prefix}{key}"
    if key == "ornek":
        return mark_safe(smooth_tile("ornek", spec.get("colors") or THREAD, label, pid, css))
    if "grid" in spec:
        pattern = from_rows(spec["grid"], {"#": 0, "o": 1})
    elif key in SYMBOL_MOTIFS:
        pattern = SYMBOL_MOTIFS[key]()
    else:
        return ""
    return mark_safe(stitch_tile(pattern, spec.get("colors") or THREAD, label, pid, css=css))


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
                    "art": _art(sym["key"], sym["name"]),
                    "hero_art": _art(sym["key"], sym["name"], prefix="h"),
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
        "date_published": data()["date_published"],
        "date_modified": data()["date_modified"],
        "updated": date.fromisoformat(data()["date_modified"]),
        "groups": groups,
        "table": rows,
        "toc": toc,
        "ornek_art": _art("ornek", content["ornek_title"]),
        "ornek_region_links": _regions(content["ornek_regions"], by_slug),
        "terms": [
            {"key": s["key"], "name": s["name"], "description": " ".join(s["text"])}
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
    out += ["", f"### {c['ornek_title']}", *map(strip_tags, c["ornek"])]
    out += [f"- {a}: {b}" for a, b in c["ornek_rows"]]
    out += ["", f"### {c['names_title']}", *c["names"], "", f"### {c['new_title']}", *c["new"]]
    out += ["", f"### {c['why_title']}", *c["why"], "", f"### {c['faq_title']}"]
    for q, a in c["faq"]:
        out += [f"**{q}**", a]
    return "\n\n".join(p for p in out if p is not None)
