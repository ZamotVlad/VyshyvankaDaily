from datetime import date, datetime, timedelta

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from apps.patterns.models import DailyPattern, Region, SavedPattern
from apps.patterns.services.generation import CURRENT_ALGORITHM_VERSION, generate_daily_pattern
from apps.patterns.services.pattern_builder import build_svg_for_date

RIBBON_DAYS = 7
ARCHIVE_PAGE_SIZE = 12


def _is_saved_by(user, pattern):
    if not user.is_authenticated:
        return False
    return SavedPattern.objects.filter(user=user, pattern=pattern).exists()


def home_view(request):
    today = timezone.localdate()
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
        "is_saved": _is_saved_by(request.user, pattern),
    }
    return render(request, "patterns/home.html", context)


def pattern_detail_view(request, iso_date):
    try:
        pattern_date = date.fromisoformat(iso_date)
    except ValueError as exc:
        raise Http404("Формат дати: YYYY-MM-DD") from exc

    if pattern_date > timezone.localdate():
        raise Http404("Дата в майбутньому")

    pattern = get_object_or_404(
        DailyPattern.objects.select_related("region").prefetch_related("motifs_used"),
        date=pattern_date,
    )

    previous_pattern = DailyPattern.objects.filter(date__lt=pattern_date).order_by("-date").first()
    next_pattern = (
        DailyPattern.objects.filter(date__gt=pattern_date, date__lte=timezone.localdate())
        .order_by("date")
        .first()
    )

    context = {
        "pattern": pattern,
        "claim_type": pattern.region.get_claim_type(),
        "previous_pattern": previous_pattern,
        "next_pattern": next_pattern,
        "is_saved": _is_saved_by(request.user, pattern),
    }
    return render(request, "patterns/pattern_detail.html", context)


@login_required
@require_POST
def toggle_save_view(request, iso_date):
    """
    Збереження/видалення патерну з колекції (розділ 5.1, 5.3, 9.1 ТЗ).

    Toggle через get_or_create/delete — покладаємось на UniqueConstraint
    (user, pattern) із Stage 1, не перевіряємо існування вручну заздалегідь.
    """
    try:
        pattern_date = date.fromisoformat(iso_date)
    except ValueError as exc:
        raise Http404("Формат дати: YYYY-MM-DD") from exc

    pattern = get_object_or_404(DailyPattern, date=pattern_date)

    saved, created = SavedPattern.objects.get_or_create(user=request.user, pattern=pattern)
    if not created:
        saved.delete()
        messages.info(request, "Видалено з колекції.")
    else:
        messages.success(request, "Збережено в колекцію.")

    next_url = request.POST.get("next") or reverse("patterns:pattern_detail", args=[iso_date])
    return redirect(next_url)


@login_required
def my_collection_view(request):
    """
    Моя колекція (розділ 9.1, 9.3 ТЗ) — виключно приватна: фільтр за
    request.user завжди, немає жодного URL-параметра з ідентифікатором
    іншого користувача, тому "чужа колекція" фізично недосяжна за
    дизайном, не лише перевіркою прав.
    """
    saved_patterns = (
        SavedPattern.objects.filter(user=request.user)
        .select_related("pattern", "pattern__region")
        .order_by("-created_at")
    )
    context = {
        "saved_patterns": saved_patterns,
        "total_saved": saved_patterns.count(),
    }
    return render(request, "patterns/my_collection.html", context)


def region_detail_view(request, slug):
    region = get_object_or_404(Region, slug=slug)

    patterns = DailyPattern.objects.filter(region=region, date__lte=timezone.localdate()).order_by(
        "-date"
    )

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
    today = timezone.localdate()
    patterns = DailyPattern.objects.filter(date__lte=today).select_related("region")

    region_slug = request.GET.get("region", "")
    if region_slug:
        region = Region.objects.verified().filter(slug=region_slug).first()
        if region is not None:
            patterns = patterns.filter(region=region)

    date_from = _parse_date_param(request.GET.get("date_from"))
    date_to = _parse_date_param(request.GET.get("date_to"))
    if date_from:
        patterns = patterns.filter(date__gte=date_from)
    if date_to:
        patterns = patterns.filter(date__lte=date_to)

    sort = request.GET.get("sort")
    if sort == "region":
        patterns = patterns.order_by("region__name", "-date")
    else:
        sort = "date"
        patterns = patterns.order_by("-date")

    paginator = Paginator(patterns, ARCHIVE_PAGE_SIZE)
    page_obj = paginator.get_page(request.GET.get("page"))

    context = {
        "page_obj": page_obj,
        "regions": Region.objects.verified().order_by("name"),
        "selected_region_slug": region_slug,
        "date_from": request.GET.get("date_from", ""),
        "date_to": request.GET.get("date_to", ""),
        "sort": sort,
    }
    return render(request, "patterns/archive.html", context)


def debug_pattern_view(request, iso_date):
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
