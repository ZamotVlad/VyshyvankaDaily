from datetime import date, timedelta

from django.conf import settings
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, render

from apps.patterns.models import DailyPattern, Region
from apps.patterns.services.generation import CURRENT_ALGORITHM_VERSION, generate_daily_pattern
from apps.patterns.services.pattern_builder import build_svg_for_date

RIBBON_DAYS = 7


def home_view(request):
    """
    Головна сторінка (розділ 5.1 ТЗ) — лінива генерація патерну на сьогодні.
    """
    today = date.today()
    pattern = generate_daily_pattern(
        today,
        algorithm_version=CURRENT_ALGORITHM_VERSION,
        generate_fn=build_svg_for_date,
    )

    ribbon = (
        DailyPattern.objects.filter(date__lte=today, date__gt=today - timedelta(days=RIBBON_DAYS))
        .select_related("region")
        .order_by("-date")
    )

    context = {
        "pattern": pattern,
        "claim_type": pattern.region.get_claim_type(),
        "ribbon": ribbon,
    }
    return render(request, "patterns/home.html", context)


def pattern_detail_view(request, iso_date):
    """
    Сторінка конкретного патерну (розділ 5.3 ТЗ).

    Захист від запиту майбутньої дати — 404, не 500. Читає вже існуючий
    запис (get_object_or_404), не генерує сам — генерація лише через
    головну сторінку (розділ 11.2).
    """
    try:
        pattern_date = date.fromisoformat(iso_date)
    except ValueError as exc:
        raise Http404("Формат дати: YYYY-MM-DD") from exc

    if pattern_date > date.today():
        raise Http404("Дата в майбутньому")

    pattern = get_object_or_404(
        DailyPattern.objects.select_related("region").prefetch_related("motifs_used"),
        date=pattern_date,
    )

    previous_pattern = DailyPattern.objects.filter(date__lt=pattern_date).order_by("-date").first()
    next_pattern = (
        DailyPattern.objects.filter(date__gt=pattern_date, date__lte=date.today())
        .order_by("date")
        .first()
    )

    context = {
        "pattern": pattern,
        "claim_type": pattern.region.get_claim_type(),
        "previous_pattern": previous_pattern,
        "next_pattern": next_pattern,
    }
    return render(request, "patterns/pattern_detail.html", context)


def region_detail_view(request, slug):
    """
    Сторінка регіону (розділ 5.4 ТЗ) — публічна освітня сторінка, SEO-актив.

    get_object_or_404 без .verified() навмисно: якщо регіон існував і
    мав опубліковані патерни, але потім деактивований чи знятий з
    верифікації — стара сторінка не повинна раптом стати 404 (посилання
    в соцмережах/пошуку лишаються живими), контент лишається доступним
    для читання, просто регіон більше не бере участі в новій ротації
    (розділ 8.3 стосується лише вибору для НОВИХ патернів, не видимості
    вже опублікованої сторінки).
    """
    region = get_object_or_404(Region, slug=slug)

    patterns = DailyPattern.objects.filter(region=region, date__lte=date.today()).order_by("-date")

    context = {
        "region": region,
        "claim_type": region.get_claim_type(),
        "patterns": patterns,
    }
    return render(request, "patterns/region_detail.html", context)


def debug_pattern_view(request, iso_date):
    """
    Тимчасова debug-сторінка (пункт "емоційний чекпоінт", Stage 1 Roadmap).
    Не публічний view — лише для власної перевірки під час розробки.
    """
    if not settings.DEBUG:
        raise Http404

    try:
        pattern_date = date.fromisoformat(iso_date)
    except ValueError as exc:
        raise Http404("Формат дати: YYYY-MM-DD") from exc

    pattern = generate_daily_pattern(
        pattern_date,
        algorithm_version=CURRENT_ALGORITHM_VERSION,
        generate_fn=build_svg_for_date,
    )

    html = f"""<!DOCTYPE html>
<html lang="uk">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Debug: {pattern.date}</title>
<style>
  body {{ font-family: sans-serif; padding: 20px; }}
  .pattern-wrap {{ max-width: 500px; border: 1px solid #ccc; margin-top: 20px; }}
  svg {{ width: 100%; height: auto; display: block; }}
</style>
</head>
<body>
<h1>{pattern.date} — {pattern.region}</h1>
<p>Статус: {pattern.generation_status}</p>
<div class="pattern-wrap">{pattern.svg_content}</div>
</body>
</html>"""
    return HttpResponse(html)
