import logging
from datetime import date, timedelta

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
from django.utils.formats import date_format
from django.utils.html import strip_tags
from django.utils.http import url_has_allowed_host_and_scheme
from django.utils.text import Truncator
from django.utils.translation import get_language
from django.utils.translation import gettext as _
from django.views.decorators.http import require_POST

from apps.blog.models import Author
from apps.core.toc import build_toc
from apps.patterns.models import DailyPattern, Region, SavedPattern
from apps.patterns.region_groups import grouped_regions
from apps.patterns.services.gen2.catalog import region_tiles
from apps.patterns.services.generation import (
    CURRENT_ALGORITHM_VERSION,
    NoFallbackAvailable,
    generate_daily_pattern,
)
from apps.patterns.services.pattern_builder import build_svg_for_date
from apps.patterns.services.region_map import build_region_map
from apps.patterns.services.rotation import get_region_for_date
from apps.patterns.services.symbols import build_page as build_symbols_page

logger = logging.getLogger(__name__)

RIBBON_DAYS = 7
ARCHIVE_PAGE_SIZE = 10
LIST_PAGE_SIZE = 12


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


LATEST_POSTS = 3

FAQ_HOME_QUESTIONS = [
    "Звідки береться орнамент, який показує сайт щодня?",
    "Чому орнамент змінюється, якщо регіон повторюється?",
    "Навіщо реєструватися, якщо орнамент дня доступний і без акаунта?",
]


def home_view(request):
    from apps.pages.models import FAQItem

    today = timezone.localdate()
    try:
        pattern = generate_daily_pattern(
            today,
            algorithm_version=CURRENT_ALGORITHM_VERSION,
            generate_fn=build_svg_for_date,
        )
    except (Region.DoesNotExist, NoFallbackAvailable):
        logger.exception("Орнамент дня недоступний на %s", today)
        return render(request, "patterns/home_unavailable.html", status=503)

    ribbon = (
        DailyPattern.objects.filter(date__lte=today, date__gt=today - timedelta(days=RIBBON_DAYS))
        .select_related("region")
        .order_by("-date")
    )

    faq_highlights = list(FAQItem.objects.filter(question_uk__in=FAQ_HOME_QUESTIONS))
    faq_highlights.sort(key=lambda item: FAQ_HOME_QUESTIONS.index(item.question_uk))

    from apps.blog.models import BlogPost

    latest_posts = list(
        BlogPost.objects.filter(status=BlogPost.Status.PUBLISHED)
        .select_related("category")
        .order_by(F("published_at").desc(nulls_last=True), "-pk")[:LATEST_POSTS]
    )

    context = {
        "pattern": pattern,
        "claim_type": pattern.region.get_claim_type(),
        "ribbon": ribbon,
        "is_saved": _is_saved_by(request.user, pattern),
        "faq_highlights": faq_highlights,
        "latest_posts": latest_posts,
        "region_groups": grouped_regions(Region.objects.verified().order_by("rotation_order")),
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


def pattern_svg_view(request, iso_date):
    """SVG орнаменту як окремий файл: мініатюри кешуються браузером, HTML легшає."""
    pattern = get_object_or_404(DailyPattern, date=_parse_iso_date(iso_date))
    response = HttpResponse(pattern.svg_content, content_type="image/svg+xml; charset=utf-8")
    # URL містить ?v=<updated_at>, тож вміст за адресою не змінюється
    response["Cache-Control"] = "public, max-age=31536000, immutable"
    return response


def _pattern_description(pattern, limit=155):
    prefix = _("Орнамент дня %(date)s: %(region)s.") % {
        "date": date_format(pattern.date, "j E Y"),
        "region": pattern.region.name,
    }
    region = pattern.region
    rest = strip_tags(region.seo_description or region.symbolism_description)
    return f"{prefix} {Truncator(rest).chars(limit - len(prefix) - 1)}"


def pattern_detail_view(request, iso_date):
    pattern_date = _parse_iso_date(iso_date)

    if pattern_date > timezone.localdate():
        raise Http404("Дата в майбутньому")

    pattern = (
        DailyPattern.objects.select_related("region")
        .prefetch_related("motifs_used")
        .filter(date=pattern_date)
        .first()
    )
    if pattern is None:
        # Старі дні не зберігаємо: ведемо на сторінку регіону того дня.
        try:
            region = get_region_for_date(pattern_date)
        except Region.DoesNotExist:
            raise Http404 from None
        return redirect("patterns:region_detail", slug=region.slug)

    previous_pattern = DailyPattern.objects.filter(date__lt=pattern_date).order_by("-date").first()
    next_pattern = (
        DailyPattern.objects.filter(date__gt=pattern_date, date__lte=timezone.localdate())
        .order_by("date")
        .first()
    )

    context = {
        "pattern": pattern,
        "meta_description": _pattern_description(pattern),
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
    Збереження/видалення патерну з колекції.

    Toggle через get_or_create/delete - покладаємось на UniqueConstraint
    (user, pattern) із Stage 1, не перевіряємо існування вручну заздалегідь.
    """
    pattern_date = _parse_iso_date(iso_date)
    pattern = get_object_or_404(DailyPattern, date=pattern_date)

    saved, created = SavedPattern.objects.get_or_create(user=request.user, pattern=pattern)
    if created:
        _update_streak(request.user.profile)
    if not created:
        saved.delete()
        messages.info(request, _("Видалено з колекції."))
    else:
        messages.success(request, _("Збережено в колекцію."))

    next_url = request.POST.get("next")
    if not url_has_allowed_host_and_scheme(
        next_url, allowed_hosts={request.get_host()}, require_https=request.is_secure()
    ):
        next_url = reverse("patterns:pattern_detail", args=[iso_date])
    return redirect(next_url)


@login_required
def my_collection_view(request):
    """
    Моя колекція - виключно приватна.

    "Пройдений тур" рахує лише збереження
    день-в-день (SavedPattern.created_at, обрізане до дати за поточним
    часовим поясом, == DailyPattern.date) - не всі збереження підряд.
    Інакше людина могла б пройти "100% туру" за один прохід архіву,
    що суперечить суті щоденного ритуалу.
    """
    saved_patterns = (
        SavedPattern.objects.filter(user=request.user)
        .select_related("pattern", "pattern__region")
        .order_by("-created_at")
    )

    tour_completed, tour_total = _tour_progress(request.user)
    page = Paginator(saved_patterns, LIST_PAGE_SIZE).get_page(request.GET.get("page"))

    context = {
        "saved_patterns": page,
        "total_saved": page.paginator.count,
        "tour_completed": tour_completed,
        "tour_total": tour_total,
    }
    return render(request, "patterns/my_collection.html", context)


def region_detail_view(request, slug):
    region = get_object_or_404(Region, slug=slug)

    body, toc = build_toc(
        region.symbolism_description,
        reserved=("articles", "motifs", "colors", "sources", "gallery"),
    )
    region_posts = list(region.published_blog_posts)
    if region_posts:
        toc.append({"id": "articles", "title": _("Статті про цей регіон")})
    lang = "en" if (get_language() or "").startswith("en") else "uk"
    motif_groups = region_tiles(region.slug, lang)
    if motif_groups:
        toc.append({"id": "motifs", "title": _("Мотиви вишивки")})
    toc.append({"id": "colors", "title": _("Домінуючі кольори")})
    if region.sources.exists():
        toc.append({"id": "sources", "title": _("Джерела")})

    context = {
        "region": region,
        "body": body,
        "toc": toc,
        "region_posts": region_posts,
        "claim_type": region.get_claim_type(),
        "photos": [p for p in region.photos.all() if p.is_active],
        "site_author": Author.objects.first(),
        "motif_groups": motif_groups,
        "symbols_url": reverse("patterns:symbols"),
    }
    return render(request, "patterns/region_detail.html", context)


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
<h1>{pattern.date} - {pattern.region}</h1>
<p>Статус: {pattern.generation_status}</p>
<div class="pattern-wrap">{pattern.svg_content}</div>
</body>
</html>"""
    return HttpResponse(html)


def _types_article_url():
    from apps.blog.models import BlogPost

    slug = "vydy-vyshyvanok"
    if BlogPost.objects.filter(slug=slug, status=BlogPost.Status.PUBLISHED).exists():
        return reverse("blog:detail", args=[slug])
    return reverse("blog:list")


def region_list_view(request):
    """
    Перелік усіх верифікованих регіонів із мапою.
    """
    regions = list(Region.objects.verified().order_by("name"))
    try:
        today_slug = get_region_for_date(timezone.localdate()).slug
    except Region.DoesNotExist:
        today_slug = ""

    def region_map():
        # Викликається лише з шаблону, коли кешу мапи ще немає.
        with_motifs = Region.objects.verified().prefetch_related("compatible_motifs")
        return build_region_map(with_motifs, today_slug)

    return render(
        request,
        "patterns/region_list.html",
        {
            "regions": regions,
            "region_groups": grouped_regions(regions),
            "region_map": region_map,
            "today_slug": today_slug,
            "symbols_url": reverse("patterns:symbols"),
            "types_url": _types_article_url(),
        },
    )


def debug_all_regions_view(request):
    """
    Галерея всіх регіонів одразу, для розробки. Викликає build_svg_for_date напряму з конкретним
    регіоном, минаючи ротацію й DailyPattern - нічого не зберігає
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


def symbols_view(request):
    page = build_symbols_page(request.LANGUAGE_CODE)
    return render(
        request,
        "patterns/symbols.html",
        {"page": page, "toc": page["toc"], "breadcrumbs": [{"label": page["nav_label"]}]},
    )
