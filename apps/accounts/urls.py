from django.urls import path

from apps.accounts import views

app_name = "accounts"

urlpatterns = [
    path("profile/settings/", views.profile_settings_view, name="profile_settings"),
]
