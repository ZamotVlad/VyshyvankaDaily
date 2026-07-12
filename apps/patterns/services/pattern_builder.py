from datetime import date

from apps.patterns.models import Region
from apps.patterns.services.seed import get_rng
from apps.patterns.services.svg_render import render_pattern_svg


def build_svg_for_date(pattern_date: date, region: Region):
    """
    generate_fn для generate_daily_pattern (Блок В).

    .order_by("pk") — критично для детермінованості (виявлено рецензією):
    QuerySet без явного порядку не гарантує стабільну послідовність між
    викликами чи СУБД (SQLite в dev може випадково "щастити", Postgres —
    ні). rng.sample() бере елементи за позицією в списку — нестабільний
    порядок ламає детермінованість сервісу генерації непомітно.
    """
    motifs = list(region.compatible_motifs.verified().order_by("pk"))
    if not motifs:
        raise ValueError(f"У регіону {region} немає жодного верифікованого мотиву.")

    rng = get_rng(pattern_date)
    selected = rng.sample(motifs, k=min(len(motifs), 3))

    return render_pattern_svg(region, selected), selected
