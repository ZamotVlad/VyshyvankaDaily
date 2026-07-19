from datetime import timedelta

from django.contrib.auth import get_user_model
from django.db.models import Count
from django.utils import timezone

from apps.blog.models import BlogPost, GuestPostSubmission
from apps.patterns.models import DailyPattern, Motif, Region, SavedPattern


def dashboard_callback(request, context):
    """
    Дашборд адмінки (розділ 14.3 ТЗ) — 6 віджетів (пункт "непрочитані
    звернення" видалений разом із ContactMessage, Частина 2 DECISIONS.md).
    """
    User = get_user_model()
    week_ago = timezone.now() - timedelta(days=7)

    total_users = User.objects.count()
    new_users_week = User.objects.filter(date_joined__gte=week_ago).count()

    pending_guest_posts = GuestPostSubmission.objects.filter(
        review_status=GuestPostSubmission.ReviewStatus.NEW
    ).count()

    saved_by_region = (
        SavedPattern.objects.values("pattern__region__name")
        .annotate(total=Count("id"))
        .order_by("-total")[:10]
    )

    editorial_debt = (
        Region.objects.exclude(verification_status=Region.VerificationStatus.VERIFIED).count()
        + Motif.objects.exclude(verification_status=Motif.VerificationStatus.VERIFIED).count()
    )

    generation_errors = DailyPattern.objects.filter(
        generation_status=DailyPattern.GenerationStatus.FALLBACK
    ).count()

    recent_posts = BlogPost.objects.filter(status=BlogPost.Status.PUBLISHED).order_by(
        "-published_at"
    )[:5]

    context.update(
        {
            "vd_total_users": total_users,
            "vd_new_users_week": new_users_week,
            "vd_pending_guest_posts": pending_guest_posts,
            "vd_saved_by_region": list(saved_by_region),
            "vd_editorial_debt": editorial_debt,
            "vd_generation_errors": generation_errors,
            "vd_recent_posts": recent_posts,
        }
    )
    return context
