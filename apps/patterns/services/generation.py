import logging
from collections.abc import Callable
from datetime import date

from django.db import IntegrityError, transaction

from apps.patterns.models import DailyPattern, Region
from apps.patterns.services.rotation import get_region_for_date
from apps.patterns.services.seed import date_to_seed

logger = logging.getLogger(__name__)

GenerateFn = Callable[[date, Region], tuple]

CURRENT_ALGORITHM_VERSION = 1


class NoFallbackAvailable(Exception):
    """Немає жодного попереднього успішного патерну для резервного сценарію."""


def _get_existing_pattern(pattern_date: date) -> DailyPattern | None:
    return DailyPattern.objects.filter(date=pattern_date).first()


def _create_success(
    pattern_date: date, region: Region, seed: str, algorithm_version: int, svg_content, motifs
) -> DailyPattern:
    with transaction.atomic():
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


def _create_fallback(pattern_date: date, seed: str) -> DailyPattern:
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

    with transaction.atomic():
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


def generate_daily_pattern(
    pattern_date: date,
    algorithm_version: int,
    generate_fn: GenerateFn,
) -> DailyPattern:
    """
    Отримати чи згенерувати DailyPattern на дату (розділ 8.1, 8.6, 11.2 ТЗ).

    Захист від гонки запитів (розділ 11.2): якщо між першою перевіркою й
    create() інший паралельний запит уже вставив запис на цю дату —
    UniqueConstraint на полі date кине IntegrityError, ми його ловимо й
    просто читаємо вже створений запис, не намагаючись створити другий.
    """
    existing = _get_existing_pattern(pattern_date)
    if existing:
        return existing

    region = get_region_for_date(pattern_date)
    seed = date_to_seed(pattern_date)

    try:
        svg_content, motifs = generate_fn(pattern_date, region)
    except Exception:
        logger.exception("Генерація патерну на %s завершилась помилкою", pattern_date)
        try:
            return _create_fallback(pattern_date, seed)
        except IntegrityError:
            return _get_existing_pattern(pattern_date)

    try:
        return _create_success(pattern_date, region, seed, algorithm_version, svg_content, motifs)
    except IntegrityError:
        return _get_existing_pattern(pattern_date)


def force_regenerate_pattern(
    pattern: DailyPattern, algorithm_version: int, generate_fn: GenerateFn
) -> DailyPattern:
    """
    Примусова перегенерація для адмінки (розділ 14.4 ТЗ) — виняткові
    випадки. НЕ видаляє існуючий запис (щоб не каскадно видалити
    SavedPattern користувачів) — перезаписує поля результату на тому
    самому записі. Регіон лишається той, що вже призначений — ротація
    стосується первинного призначення дня, не форс-перегенерації.
    """
    svg_content, motifs = generate_fn(pattern.date, pattern.region)
    pattern.svg_content = svg_content
    pattern.algorithm_version = algorithm_version
    pattern.generation_status = DailyPattern.GenerationStatus.SUCCESS
    pattern.save()
    pattern.motifs_used.set(motifs)
    return pattern
