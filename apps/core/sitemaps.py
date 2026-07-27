from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from apps.blog.models import BlogPost
from apps.patterns.models import DailyPattern, Region


class DailyPatternSitemap(Sitemap):
    """Кожен орнамент дня - головний обсяг контенту сайту."""

    changefreq = "never"  # опублікований день не змінюється
    priority = 0.6
    i18n = True
    alternates = True
    x_default = True

    def items(self):
        return DailyPattern.objects.order_by("-date")

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


class StaticViewSitemap(Sitemap):
    """Сторінки без моделі - фіксований список іменованих URL."""

    changefreq = "yearly"
    priority = 0.5
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

    def location(self, item):
        return reverse(item)
