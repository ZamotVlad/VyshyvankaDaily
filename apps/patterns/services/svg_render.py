from apps.patterns.models import Motif, Region
from apps.patterns.services.geometry import apply_symmetry

SHIRT_VIEWBOX = "0 0 400 500"

SHIRT_OUTLINE = (
    "M100,100 L170,100 L200,130 L230,100 L300,100 "
    "L360,140 L360,220 L300,190 L300,450 L100,450 "
    "L100,190 L40,220 L40,140 Z"
)

# Зони вишивки (розділ 8.5 ТЗ). Тимчасовий дизайн (ADR 12) — замінюється в Stage 2/6.
EMBROIDERY_ZONES = {
    "collar": {"x": 150, "y": 95, "width": 100, "height": 20},
    "placket": {"x": 185, "y": 120, "width": 30, "height": 300},
    "cuff_left": {"x": 40, "y": 195, "width": 60, "height": 20},
    "cuff_right": {"x": 300, "y": 195, "width": 60, "height": 20},
    "hem": {"x": 100, "y": 420, "width": 200, "height": 25},
}


def _render_motif_in_zone(motif: Motif, zone: dict, fill_color: str) -> str:
    geometry = motif.geometry_parameters
    shapes = apply_symmetry(
        geometry["base_points"], geometry["symmetry"], geometry.get("params", {})
    )

    all_points = [p for shape in shapes for p in shape]
    xs = [p[0] for p in all_points]
    ys = [p[1] for p in all_points]
    span_x = max(max(xs) - min(xs), 1)
    span_y = max(max(ys) - min(ys), 1)

    polygons = []
    for shape in shapes:
        scaled = [
            (
                zone["x"] + (x - min(xs)) / span_x * zone["width"],
                zone["y"] + (y - min(ys)) / span_y * zone["height"],
            )
            for x, y in shape
        ]
        coords = " ".join(f"{x:.2f},{y:.2f}" for x, y in scaled)
        polygons.append(f'<polygon points="{coords}" fill="{fill_color}" />')

    return "".join(polygons)


def render_pattern_svg(region: Region, motifs: list[Motif]) -> str:
    """
    SVG орнаменту дня (розділ 8.5, 8.7 ТЗ): силует + мотиви на зонах.

    Спрощений розподіл Stage 1 — мотиви циклічно по зонах (застереження
    Roadmap), розширюється пізніше.
    """
    zone_names = list(EMBROIDERY_ZONES.keys())
    colors = region.dominant_colors or ["#000000"]

    motif_elements = [
        _render_motif_in_zone(
            motif, EMBROIDERY_ZONES[zone_names[i % len(zone_names)]], colors[i % len(colors)]
        )
        for i, motif in enumerate(motifs)
    ]

    return (
        f'<svg viewBox="{SHIRT_VIEWBOX}" xmlns="http://www.w3.org/2000/svg" '
        f'role="img" aria-label="Орнамент {region.name}">'
        f'<path d="{SHIRT_OUTLINE}" fill="#FFFFFF" stroke="#333333" stroke-width="2"/>'
        f"{''.join(motif_elements)}"
        f"</svg>"
    )
