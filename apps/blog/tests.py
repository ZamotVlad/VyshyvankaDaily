from django.core.cache import cache
from django.test import TestCase

from apps.blog.models import BlogCategory, BlogPost, GuestPostSubmission


class GuestPostSubmissionTests(TestCase):
    def _valid_data(self, honeypot=""):
        return {
            "contact_name": "Тест Тестенко",
            "email": "test@example.com",
            "brand_name": "",
            "proposed_topic": "Тестова тема",
            "proposal_description": "Опис пропозиції.",
            "honeypot": honeypot,
        }

    def test_valid_submission_creates_record(self):
        self.client.post("/blog/propose/", self._valid_data())
        self.assertEqual(GuestPostSubmission.objects.count(), 1)

    def test_honeypot_filled_silently_rejects(self):
        response = self.client.post("/blog/propose/", self._valid_data(honeypot="я бот"))
        self.assertEqual(GuestPostSubmission.objects.count(), 0)
        self.assertEqual(response.status_code, 302)  # той самий "успіх", що й для людини

    def test_rate_limit_blocks_after_threshold(self):
        for _ in range(3):
            self.client.post("/blog/propose/", self._valid_data())
        response = self.client.post("/blog/propose/", self._valid_data())
        self.assertEqual(response.status_code, 403)

    def setUp(self):
        cache.clear()


class BlogPostSanitizationTests(TestCase):
    def test_disallowed_tags_stripped_on_save(self):
        post = BlogPost.objects.create(
            title="Тест",
            excerpt="Опис",
            body="<p>Текст</p><script>alert(1)</script>",
            category=BlogCategory.objects.create(name="Категорія"),
        )
        self.assertNotIn("<script>", post.body)
        self.assertIn("<p>Текст</p>", post.body)
