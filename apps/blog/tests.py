from django.core.cache import cache
from django.test import TestCase
from django.utils import timezone

from apps.blog.models import BlogCategory, BlogPost, GuestPostSubmission
from apps.patterns.models import Region


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


class BlogSearchTests(TestCase):
    def setUp(self):
        self.category = BlogCategory.objects.create(
            name_uk="Дослідження", slug="research", is_active=True
        )
        self.post = BlogPost.objects.create(
            title_uk="Символіка Полтавщини",
            slug="poltava-symbolism",
            excerpt_uk="Про техніку білим по білому",
            body="<p>Текст</p>",
            category=self.category,
            status="published",
            published_at=timezone.now(),
        )
        BlogPost.objects.create(
            title_uk="Чернетка про Волинь",
            slug="volyn-draft",
            excerpt_uk="Ще не готово",
            body="<p>Текст</p>",
            category=self.category,
            status="draft",
        )

    def test_search_finds_by_title(self):
        response = self.client.get("/blog/?q=Полтавщини")
        self.assertContains(response, "Символіка Полтавщини")

    def test_search_finds_by_excerpt(self):
        response = self.client.get("/blog/?q=білим")
        self.assertContains(response, "Символіка Полтавщини")

    def test_search_never_returns_drafts(self):
        response = self.client.get("/blog/?q=Волинь")
        self.assertNotContains(response, "Чернетка про Волинь")

    def test_empty_search_returns_all_published(self):
        response = self.client.get("/blog/?q=")
        self.assertContains(response, "Символіка Полтавщини")

    def test_search_preserves_category_filter(self):
        response = self.client.get(f"/blog/?q=Полтавщини&category={self.category.slug}")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Символіка Полтавщини")


class RegionLinkingTests(TestCase):
    def setUp(self):
        self.region = Region.objects.create(
            name_uk="Тестовий регіон",
            slug="test-region",
            verification_status="verified",
            is_active=True,
            rotation_order=99,
            dominant_colors=["#000000"],
        )
        self.category = BlogCategory.objects.create(name_uk="Категорія", slug="cat", is_active=True)

    def test_published_post_appears_on_region_page(self):
        BlogPost.objects.create(
            title_uk="Опублікована стаття",
            slug="published-one",
            body="<p>x</p>",
            category=self.category,
            status="published",
            published_at=timezone.now(),
            related_region=self.region,
        )
        response = self.client.get(f"/regions/{self.region.slug}/")
        self.assertContains(response, "Опублікована стаття")

    def test_draft_post_never_appears_on_region_page(self):
        """Найважливіший тест блоку: чернетка не повинна витікати
        на публічну сторінку регіону через зворотний зв'язок."""
        BlogPost.objects.create(
            title_uk="Секретна чернетка",
            slug="secret-draft",
            body="<p>x</p>",
            category=self.category,
            status="draft",
            related_region=self.region,
        )
        response = self.client.get(f"/regions/{self.region.slug}/")
        self.assertNotContains(response, "Секретна чернетка")

    def test_region_page_works_without_any_posts(self):
        response = self.client.get(f"/regions/{self.region.slug}/")
        self.assertEqual(response.status_code, 200)
