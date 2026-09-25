from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from django.utils import timezone

from apps.blog.models import Author, BlogPost
from apps.patterns.models import DailyPattern, Region


class DailyPatternSitemap(Sitemap):
    """Кожен орнамент дня - головний обсяг контенту сайту."""

    changefreq = "never"  # опублікований день не змінюється
    priority = 0.6
    i18n = True
    alternates = True
    x_default = True

    def items(self):
        # Тільки сьогоднішній патерн - минулі дні майже дублюють контент
        # сторінки регіону (symbolism_description, motifs, sources), тому
        # закриті від індексації (noindex у шаблоні) і не мають бути в
        # sitemap - не варто витрачати краулінговий бюджет робота на них.
        return DailyPattern.objects.filter(date=timezone.localdate())

    def location(self, obj):
        return reverse("patterns:pattern_detail", args=[obj.date.isoformat()])

    def lastmod(self, obj):
        return obj.updated_at


class RegionSitemap(Sitemap):
    """27 сторінок регіонів - основний SEO-хаб проєкту."""

    changefreq = "monthly"
    priority = 0.9
    i18n = True
    alternates = True
    x_default = True

    def items(self):
        return Region.objects.verified().order_by("name")

    def location(self, obj):
        return reverse("patterns:region_detail", args=[obj.slug])

    def lastmod(self, obj):
        return obj.updated_at


class BlogPostSitemap(Sitemap):
    changefreq = "monthly"
    priority = 0.7
    i18n = True
    alternates = True
    x_default = True

    def items(self):
        return BlogPost.objects.filter(status=BlogPost.Status.PUBLISHED).order_by("-published_at")

    def location(self, obj):
        return reverse("blog:detail", args=[obj.slug])

    def lastmod(self, obj):
        return obj.updated_at


class AuthorSitemap(Sitemap):
    changefreq = "monthly"
    priority = 0.4
    i18n = True
    alternates = True
    x_default = True

    def items(self):
        return Author.objects.order_by("name")

    def location(self, obj):
        return reverse("blog:author_detail", args=[obj.slug])

    def lastmod(self, obj):
        return obj.updated_at


class StaticViewSitemap(Sitemap):
    """Сторінки без моделі - фіксований список іменованих URL."""

    i18n = True
    alternates = True
    x_default = True

    def items(self):
        return [
            "patterns:home",
            "patterns:archive",
            "patterns:region_list",
            "blog:list",
            "pages:about",
            "pages:faq",
            "pages:contact",
            "pages:terms",
            "pages:privacy",
        ]

    def changefreq(self, item):
        # Головна показує сьогоднішній патерн - реально оновлюється щодня.
        return "daily" if item == "patterns:home" else "yearly"

    def priority(self, item):
        return 1.0 if item == "patterns:home" else 0.5

    def location(self, item):
        return reverse(item)
