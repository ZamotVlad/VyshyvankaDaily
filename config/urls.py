from django.conf import settings
from django.conf.urls.i18n import i18n_patterns
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.urls import include, path

from apps.blog.feeds import BlogFeed
from apps.core.sitemaps import (
    BlogPostSitemap,
    DailyPatternSitemap,
    RegionSitemap,
    StaticViewSitemap,
)
from apps.core.views import robots_txt, set_language_view

sitemaps = {
    "patterns": DailyPatternSitemap,
    "regions": RegionSitemap,
    "blog": BlogPostSitemap,
    "static": StaticViewSitemap,
}

urlpatterns = [
    path("vd/", admin.site.urls),
    path("i18n/setlang/", set_language_view, name="set_language"),
    path("ckeditor5/", include("django_ckeditor_5.urls")),
    path("sitemap.xml", sitemap, {"sitemaps": sitemaps}, name="sitemap"),
    path("robots.txt", robots_txt, name="robots_txt"),
    path("blog/feed/", BlogFeed(), name="blog_feed"),
]

urlpatterns += i18n_patterns(
    path("accounts/", include("allauth.urls")),
    path("blog/", include("apps.blog.urls")),
    path("", include("apps.accounts.urls")),
    path("", include("apps.patterns.urls")),
    path("", include("apps.pages.urls")),
    prefix_default_language=False,
)

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
