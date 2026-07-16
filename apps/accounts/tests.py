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
