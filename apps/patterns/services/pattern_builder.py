from datetime import date

from apps.patterns.models import Region
from apps.patterns.services.gen2 import render_region
from apps.patterns.services.seed import get_rng


def build_svg_for_date(pattern_date: date, region: Region):
    """
    generate_fn для generate_daily_pattern (Блок В): сорочка генератора 2.0.

    .order_by("pk") - критично для детермінованості (виявлено рецензією):
    QuerySet без явного порядку не гарантує стабільну послідовність між
    викликами чи СУБД (SQLite в dev може випадково "щастити", Postgres -
    ні). rng.sample() бере елементи за позицією в списку - нестабільний
    порядок ламає детермінованість сервісу генерації непомітно.
    Мотиви з бази - підписи «Мотиви» на сторінці дня; той самий rng далі
    обирає варіанти малюнка.
    """
    motifs = list(region.compatible_motifs.verified().order_by("pk"))
    if not motifs:
        raise ValueError(f"У регіону {region} немає жодного верифікованого мотиву.")

    rng = get_rng(pattern_date)
    selected = rng.sample(motifs, k=min(len(motifs), 3))
    svg = render_region(
        region.slug, rng, f"Орнамент {region.name}", list(region.dominant_colors or [])
    )
    return svg, selected
