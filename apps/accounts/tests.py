from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.accounts.models import Profile
from apps.accounts.signals import create_profile_on_user_creation

User = get_user_model()


class ProfileSignalTests(TestCase):
    def test_profile_created_automatically_on_user_creation(self):
        user = User.objects.create_user(username="tester", password="pass12345")
        self.assertTrue(Profile.objects.filter(user=user).exists())

    def test_get_display_name_falls_back_to_username(self):
        user = User.objects.create_user(username="tester2", password="pass12345")
        profile = Profile.objects.get(user=user)
        self.assertEqual(profile.get_display_name(), "tester2")

    def test_raw_save_does_not_trigger_profile_creation(self):
        user = User(username="fixture_user")
        user.save()
        Profile.objects.filter(user=user).delete()

        create_profile_on_user_creation(sender=User, instance=user, created=True, raw=True)
        self.assertFalse(Profile.objects.filter(user=user).exists())


class ProfileSettingsViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="settingsuser", password="pass12345")

    def test_anonymous_redirected_to_login(self):
        response = self.client.get("/profile/settings/")
        self.assertEqual(response.status_code, 302)
        self.assertIn("/accounts/login/", response.url)

    def test_authenticated_can_view_settings(self):
        self.client.force_login(self.user)
        response = self.client.get("/profile/settings/")
        self.assertEqual(response.status_code, 200)

    def test_authenticated_can_update_display_name(self):
        self.client.force_login(self.user)
        self.client.post(
            "/profile/settings/",
            {"display_name": "Тестове ім'я", "default_language": ""},
        )
        self.user.profile.refresh_from_db()
        self.assertEqual(self.user.profile.display_name, "Тестове ім'я")


class DisplayedStreakTests(TestCase):
    def setUp(self):
        from django.contrib.auth import get_user_model

        self.user = get_user_model().objects.create_user(username="s", password="pass12345")
        self.profile = self.user.profile
        self.profile.current_streak = 5

    def _set_last_active(self, days_ago):
        from datetime import timedelta

        from django.utils import timezone

        self.profile.last_active_date = timezone.localdate() - timedelta(days=days_ago)
        self.profile.save()

    def test_streak_kept_if_active_today_or_yesterday(self):
        for days_ago in (0, 1):
            self._set_last_active(days_ago)
            self.assertEqual(self.profile.displayed_streak, 5)

    def test_streak_shown_as_zero_after_missed_day(self):
        self._set_last_active(2)
        self.assertEqual(self.profile.displayed_streak, 0)

    def test_home_page_shows_zero_after_missed_day(self):
        self._set_last_active(3)
        self.client.force_login(self.user)
        response = self.client.get("/")
        self.assertContains(response, "0 днів поспіль")
        self.assertNotContains(response, "5 днів поспіль")
