"""
Контури областей для мапи на /regions/ -> apps/patterns/data/region_map.json.

Джерело: Natural Earth, ne_10m_admin_1_states_provinces.geojson (суспільне надбання).
Крим і Севастополь беруться за кодами ISO UA-43 / UA-40 незалежно від того,
як їх позначено в наборі.

    pip install shapely
    python tools/build_region_map.py ne_10m_admin_1_states_provinces.geojson
"""

import argparse
import json
import math
from pathlib import Path

from shapely.geometry import shape
from shapely.ops import polylabel

ISO = {
    "UA-05": "vinnytska-oblast",
    "UA-07": "volynska-oblast",
    "UA-12": "dnipropetrovska-oblast",
    "UA-14": "donetska-oblast",
    "UA-18": "zhytomyrska-oblast",
    "UA-21": "zakarpatska-oblast",
    "UA-23": "zaporizka-oblast",
    "UA-26": "ivano-frankivska-oblast",
    "UA-32": "kyivska-oblast",
    "UA-35": "kirovohradska-oblast",
    "UA-09": "luhanska-oblast",
    "UA-46": "lvivska-oblast",
    "UA-48": "mykolaivska-oblast",
    "UA-51": "odeska-oblast",
    "UA-53": "poltavska-oblast",
    "UA-56": "rivnenska-oblast",
    "UA-59": "sumska-oblast",
    "UA-61": "ternopilska-oblast",
    "UA-63": "kharkivska-oblast",
    "UA-65": "khersonska-oblast",
    "UA-68": "khmelnytska-oblast",
    "UA-71": "cherkaska-oblast",
    "UA-77": "chernivetska-oblast",
    "UA-74": "chernihivska-oblast",
    "UA-43": "ar-krym",
    "UA-30": "m-kyiv",
    "UA-40": "m-sevastopol",
}
CITIES = ("m-kyiv", "m-sevastopol")
WIDTH = 1000
OUT = Path(__file__).resolve().parent.parent / "apps/patterns/data/region_map.json"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("geojson")
    args = parser.parse_args()
    data = json.loads(Path(args.geojson).read_text(encoding="utf-8"))
    feats = {
        ISO[f["properties"]["iso_3166_2"]]: shape(f["geometry"])
        for f in data["features"]
        if f["properties"].get("iso_3166_2") in ISO
    }
    if len(feats) != len(ISO):
        raise SystemExit(f"Знайдено {len(feats)} областей замість {len(ISO)}")

    k = math.cos(math.radians(48.5))
    minx = min(g.bounds[0] for g in feats.values())
    maxx = max(g.bounds[2] for g in feats.values())
    miny = min(g.bounds[1] for g in feats.values())
    maxy = max(g.bounds[3] for g in feats.values())
    scale = WIDTH / ((maxx - minx) * k)
    height = round((maxy - miny) * scale)

    def pt(x, y):
        return round((x - minx) * k * scale, 1), round((maxy - y) * scale, 1)

    regions = {}
    for slug, geom in sorted(feats.items()):
        geom = geom.simplify(0.004 if slug in CITIES else 0.012, preserve_topology=True)
        polys = [geom] if geom.geom_type == "Polygon" else list(geom.geoms)
        parts = []
        for poly in polys:
            if poly.area < 0.002 and slug not in CITIES:
                continue
            coords = [pt(*xy) for xy in poly.exterior.coords][:-1]
            x0, y0 = coords[0]
            steps = [f"M{x0:g} {y0:g}"]
            for (ax, ay), (bx, by) in zip(coords, coords[1:]):
                steps.append(f"{round(bx - ax, 1):g} {round(by - ay, 1):g}")
            parts.append(steps[0] + "l" + " ".join(steps[1:]) + "z")
        main = max(polys, key=lambda p: p.area)
        label = polylabel(main, tolerance=0.01)
        cx, cy = pt(label.x, label.y)
        regions[slug] = {"d": "".join(parts), "cx": cx, "cy": cy}

    OUT.write_text(
        json.dumps({"width": WIDTH, "height": height, "regions": regions}, separators=(",", ":")),
        encoding="utf-8",
    )
    print(f"{OUT}: {OUT.stat().st_size // 1024} КБ, {WIDTH}x{height}")


if __name__ == "__main__":
    main()
