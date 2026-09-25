from datetime import date, datetime, timedelta

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import F
from django.db.models.functions import TruncDate
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from apps.blog.models import Author
from apps.patterns.models import DailyPattern, Region, SavedPattern
from apps.patterns.services.generation import CURRENT_ALGORITHM_VERSION, generate_daily_pattern
from apps.patterns.services.pattern_builder import build_svg_for_date

RIBBON_DAYS = 7
ARCHIVE_PAGE_SIZE = 10


def _is_saved_by(user, pattern):
    if not user.is_authenticated:
        return False
    return SavedPattern.objects.filter(user=user, pattern=pattern).exists()


def _tour_progress(user):
    """Спільний розрахунок для home_view і my_collection_view - див. ADR 29."""
    tour_region_ids = (
        SavedPattern.objects.filter(user=user)
        .annotate(saved_date=TruncDate("created_at"))
        .filter(saved_date=F("pattern__date"))
        .values_list("pattern__region_id", flat=True)
        .distinct()
    )
    return len(tour_region_ids), Region.objects.verified().count()


FAQ_HOME_QUESTIONS = [
    "Звідки береться орнамент, який показує сайт щодня?",
    "Чому орнамент змінюється, якщо регіон повторюється?",
    "Навіщо реєструватися, якщо орнамент дня доступний і без акаунта?",
]


def home_view(request):
    from apps.pages.models import FAQItem

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

    faq_highlights = list(FAQItem.objects.filter(question_uk__in=FAQ_HOME_QUESTIONS))
    faq_highlights.sort(key=lambda item: FAQ_HOME_QUESTIONS.index(item.question_uk))

    context = {
        "pattern": pattern,
        "claim_type": pattern.region.get_claim_type(),
        "ribbon": ribbon,
        "is_saved": _is_saved_by(request.user, pattern),
        "faq_highlights": faq_highlights,
    }

    if request.user.is_authenticated:
        tour_completed, tour_total = _tour_progress(request.user)
        context["tour_completed"] = tour_completed
        context["tour_total"] = tour_total

    return render(request, "patterns/home.html", context)


def _parse_iso_date(value: str) -> date:
    """Лише канонічний YYYY-MM-DD, щоб у сторінки була одна адреса."""
    try:
        parsed = date.fromisoformat(value)
    except ValueError:
        parsed = None
    if parsed is None or parsed.isoformat() != value:
        raise Http404("Формат дати: YYYY-MM-DD")
    return parsed


def pattern_detail_view(request, iso_date):
    pattern_date = _parse_iso_date(iso_date)

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
        "is_today": pattern_date == timezone.localdate(),
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
    pattern_date = _parse_iso_date(iso_date)
    pattern = get_object_or_404(DailyPattern, date=pattern_date)

    saved, created = SavedPattern.objects.get_or_create(user=request.user, pattern=pattern)
    if created:
        _update_streak(request.user.profile)
    if not created:
        saved.delete()
        messages.info(request, "Видалено з колекції.")
    else:
        messages.success(request, "Збережено в колекцію.")

    next_url = request.POST.get("next")
    if not url_has_allowed_host_and_scheme(
        next_url, allowed_hosts={request.get_host()}, require_https=request.is_secure()
    ):
        next_url = reverse("patterns:pattern_detail", args=[iso_date])
    return redirect(next_url)


@login_required
def my_collection_view(request):
    """
    Моя колекція (розділ 9.1, 9.3 ТЗ) — виключно приватна.

    Розділ 9.2 ТЗ + уточнення: "пройдений тур" рахує лише збереження
    день-в-день (SavedPattern.created_at, обрізане до дати за поточним
    часовим поясом, == DailyPattern.date) — не всі збереження підряд.
    Інакше людина могла б пройти "100% туру" за один прохід архіву,
    що суперечить суті щоденного ритуалу.
    """
    saved_patterns = (
        SavedPattern.objects.filter(user=request.user)
        .select_related("pattern", "pattern__region")
        .order_by("-created_at")
    )

    tour_completed, tour_total = _tour_progress(request.user)

    context = {
        "saved_patterns": saved_patterns,
        "total_saved": saved_patterns.count(),
        "tour_completed": tour_completed,
        "tour_total": tour_total,
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
        "site_author": Author.objects.first(),
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


def region_list_view(request):
    """
    Перелік усіх верифікованих регіонів (не з ТЗ буквально — додано
    для навігації, оскільки контент 27 регіонів готовий, а прямого
    способу переглянути їх усі не було).
    """
    regions = Region.objects.verified().order_by("name")
    return render(request, "patterns/region_list.html", {"regions": regions})


def debug_all_regions_view(request):
    """
    Галерея всіх регіонів одразу (не з ТЗ — зручність розробки для
    Треку Б). Викликає build_svg_for_date напряму з конкретним
    регіоном, минаючи ротацію й DailyPattern — нічого не зберігає
    в базі, чистий перегляд.
    """
    if not settings.DEBUG:
        raise Http404

    today = timezone.localdate()
    results = []
    for region in Region.objects.all().order_by("rotation_order"):
        try:
            svg_content, motifs = build_svg_for_date(today, region)
        except ValueError:
            svg_content = None
            motifs = []
        results.append({"region": region, "svg": svg_content, "motifs": motifs})

    return render(request, "patterns/debug_all_regions.html", {"results": results})


def _update_streak(profile):
    """
    Streak - дні поспіль, коли людина зберігала орнамент. На відміну від
    "пройденого туру" (Stage 3, ADR 29) - не обмежений 27 регіонами й не
    застигає назавжди: рахує лише послідовність днів, регіон може
    повторюватись без шкоди для лічильника.
    """
    today = timezone.localdate()
    last = profile.last_active_date

    if last == today:
        return  # уже рахували сьогодні, повторне збереження того самого дня не множить streak
    if last == today - timedelta(days=1):
        profile.current_streak += 1
    else:
        profile.current_streak = 1  # пропущений день чи перший раз - лічильник з нуля

    profile.last_active_date = today
    profile.save()
