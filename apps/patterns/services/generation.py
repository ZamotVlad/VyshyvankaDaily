import logging
from collections.abc import Callable
from datetime import date

from apps.patterns.models import DailyPattern, Region
from apps.patterns.services.rotation import get_region_for_date
from apps.patterns.services.seed import date_to_seed

logger = logging.getLogger(__name__)

GenerateFn = Callable[[date, Region], tuple]

CURRENT_ALGORITHM_VERSION = 1


class NoFallbackAvailable(Exception):
    """Немає жодного попереднього успішного патерну для резервного сценарію."""


def generate_daily_pattern(
    pattern_date: date,
    algorithm_version: int,
    generate_fn: GenerateFn,
) -> DailyPattern:
    """
    Отримати чи згенерувати DailyPattern на дату (розділ 8.1, 8.6 ТЗ).

    generate_fn(pattern_date, region) -> (svg_content, motifs_iterable) —
    підставляється ззовні: реальна геометрія (Блок Г) ще не готова,
    цей сервіс стійкості від неї не залежить.
    """
    existing = DailyPattern.objects.filter(date=pattern_date).first()
    if existing:
        return existing

    region = get_region_for_date(pattern_date)
    seed = date_to_seed(pattern_date)

    try:
        svg_content, motifs = generate_fn(pattern_date, region)
        pattern = DailyPattern.objects.create(
            date=pattern_date,
            region=region,
            seed=seed,
            algorithm_version=algorithm_version,
            svg_content=svg_content,
            generation_status=DailyPattern.GenerationStatus.SUCCESS,
        )
        pattern.motifs_used.set(motifs)
        return pattern
    except Exception:
        logger.exception("Генерація патерну на %s завершилась помилкою", pattern_date)
        fallback_source = (
            DailyPattern.objects.filter(generation_status=DailyPattern.GenerationStatus.SUCCESS)
            .order_by("-date")
            .first()
        )
        if fallback_source is None:
            raise NoFallbackAvailable(
                f"Генерація на {pattern_date} провалилась, і немає жодного "
                "попереднього успішного патерну для резервного сценарію."
            ) from None

        pattern = DailyPattern.objects.create(
            date=pattern_date,
            region=fallback_source.region,
            seed=seed,
            algorithm_version=fallback_source.algorithm_version,
            svg_content=fallback_source.svg_content,
            generation_status=DailyPattern.GenerationStatus.FALLBACK,
        )
        pattern.motifs_used.set(fallback_source.motifs_used.all())
        return pattern
