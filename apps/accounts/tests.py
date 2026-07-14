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
        """Симуляція завантаження фікстури (raw=True) — сигнал не повинен спрацьовувати."""
        user = User(username="fixture_user")
        user.save()
        Profile.objects.filter(user=user).delete()  # прибираємо те, що створив звичайний сигнал

        create_profile_on_user_creation(sender=User, instance=user, created=True, raw=True)
        self.assertFalse(Profile.objects.filter(user=user).exists())
