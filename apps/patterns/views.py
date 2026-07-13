from datetime import date, datetime, timedelta

from django.conf import settings
from django.core.paginator import Paginator
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, render

from apps.patterns.models import DailyPattern, Region
from apps.patterns.services.generation import CURRENT_ALGORITHM_VERSION, generate_daily_pattern
from apps.patterns.services.pattern_builder import build_svg_for_date

RIBBON_DAYS = 7
ARCHIVE_PAGE_SIZE = 12


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

    get_object_or_404 без .verified() навмисно: стара пряма адреса регіону
    лишається живою навіть після деактивації (розділ 8.3 стосується лише
    вибору для НОВИХ патернів, не видимості вже опублікованої сторінки).
    """
    region = get_object_or_404(Region, slug=slug)

    patterns = DailyPattern.objects.filter(region=region, date__lte=date.today()).order_by("-date")

    context = {
        "region": region,
        "claim_type": region.get_claim_type(),
        "patterns": patterns,
    }
    return render(request, "patterns/region_detail.html", context)


def _parse_date_param(value: str | None) -> date | None:
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        return None


def archive_view(request):
    """
    Архів (розділ 5.2 ТЗ): фільтр за регіоном і діапазоном дат, пагінація.

    Фільтр за регіоном приймає лише slug активного верифікованого регіону
    (Region.objects.verified()) — неіснуючий slug чи slug деактивованого
    регіону дають порожній стан із поясненням, а не помилку й не повний
    історичний список (на відміну від прямої сторінки регіону, Блок Д).
    """
    today = date.today()
    patterns = (
        DailyPattern.objects.filter(date__lte=today).select_related("region").order_by("-date")
    )

    region_slug = request.GET.get("region", "")
    selected_region = None
    invalid_region_filter = False

    if region_slug:
        selected_region = Region.objects.verified().filter(slug=region_slug).first()
        if selected_region is None:
            invalid_region_filter = True
            patterns = DailyPattern.objects.none()
        else:
            patterns = patterns.filter(region=selected_region)

    date_from = _parse_date_param(request.GET.get("date_from"))
    date_to = _parse_date_param(request.GET.get("date_to"))
    if date_from:
        patterns = patterns.filter(date__gte=date_from)
    if date_to:
        patterns = patterns.filter(date__lte=date_to)

    paginator = Paginator(patterns, ARCHIVE_PAGE_SIZE)
    page_obj = paginator.get_page(request.GET.get("page"))

    context = {
        "page_obj": page_obj,
        "regions": Region.objects.verified().order_by("name"),
        "selected_region_slug": region_slug,
        "invalid_region_filter": invalid_region_filter,
        "date_from": request.GET.get("date_from", ""),
        "date_to": request.GET.get("date_to", ""),
    }
    return render(request, "patterns/archive.html", context)


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
