from django.urls import path

from apps.patterns import views

app_name = "patterns"

urlpatterns = [
    path("", views.home_view, name="home"),
    path("patterns/debug/<str:iso_date>/", views.debug_pattern_view, name="debug_pattern"),
]
