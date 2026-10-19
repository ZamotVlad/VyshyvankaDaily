from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from apps.blog.models import Author, BlogPost
from apps.patterns.models import Region


class ImageSitemapMixin:
    """Додає до запису sitemap фото (image sitemap) з image_urls(obj)."""

    def _urls(self, page, protocol, domain):
        urls = super()._urls(page, protocol, domain)
        for url in urls:
            obj = url["item"][0] if isinstance(url["item"], tuple) else url["item"]
            url["images"] = [
                src if src.startswith("http") else f"{protocol}://{domain}{src}"
                for src in self.image_urls(obj)
            ]
        return urls


class RegionSitemap(ImageSitemapMixin, Sitemap):
    """27 сторінок регіонів - основний SEO-хаб проєкту."""

    changefreq = "monthly"
    priority = 0.9
    i18n = True
    alternates = True
    x_default = True

    def items(self):
        return Region.objects.verified().prefetch_related("photos").order_by("name")

    def location(self, obj):
        return reverse("patterns:region_detail", args=[obj.slug])

    def lastmod(self, obj):
        return obj.updated_at

    def image_urls(self, obj):
        # Лише справжні фото з адмінки, без згенерованих орнаментів
        return [photo.image_url for photo in obj.photos.all() if photo.is_active]


class BlogPostSitemap(ImageSitemapMixin, Sitemap):
    changefreq = "monthly"
    priority = 0.7
    i18n = True
    alternates = True
    x_default = True

    def items(self):
        return BlogPost.objects.filter(status=BlogPost.Status.PUBLISHED).order_by("-published_at")

    def get_languages_for_item(self, item):
        # Без англійського тексту EN-версія статті не індексується
        return [code for code in self._languages() if code != "en" or item.has_english]

    def location(self, obj):
        return reverse("blog:detail", args=[obj.slug])

    def lastmod(self, obj):
        return obj.updated_at

    def image_urls(self, obj):
        return obj.image_urls


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
            "patterns:region_list",
            "patterns:symbols",
            "blog:list",
            "pages:about",
            "pages:sources",
            "pages:faq",
            "pages:contact",
            "pages:terms",
            "pages:privacy",
            "blog:propose",
        ]

    def changefreq(self, item):
        # Головна показує сьогоднішній патерн - реально оновлюється щодня.
        return "daily" if item == "patterns:home" else "yearly"

    def priority(self, item):
        if item == "patterns:home":
            return 1.0
        return 0.8 if item in ("patterns:region_list", "patterns:symbols") else 0.5

    def location(self, item):
        return reverse(item)
