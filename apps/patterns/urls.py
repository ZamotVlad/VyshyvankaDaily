from django.urls import path

from apps.patterns import views

app_name = "patterns"

urlpatterns = [
    path("", views.home_view, name="home"),
    path("archive/", views.archive_view, name="archive"),
    path("pattern/<str:iso_date>/", views.pattern_detail_view, name="pattern_detail"),
    path("regions/<slug:slug>/", views.region_detail_view, name="region_detail"),
    path("patterns/debug/<str:iso_date>/", views.debug_pattern_view, name="debug_pattern"),
]
