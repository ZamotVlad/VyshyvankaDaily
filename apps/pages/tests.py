# Тестів наразі немає — форма контактів видалена (Частина 2 DECISIONS.md),
# FAQ/about/terms/privacy без окремих тестових сценаріїв на цьому етапі.
from django.test import TestCase

from apps.pages.models import FAQCategory, FAQItem, StaticPage


class StaticPagesTests(TestCase):
    def test_about_page_returns_200(self):
        response = self.client.get("/about/")
        self.assertEqual(response.status_code, 200)

    def test_terms_page_returns_200(self):
        response = self.client.get("/terms-of-use/")
        self.assertEqual(response.status_code, 200)

    def test_privacy_page_returns_200(self):
        response = self.client.get("/privacy-policy/")
        self.assertEqual(response.status_code, 200)

    def test_contacts_page_returns_200(self):
        response = self.client.get("/contacts/")
        self.assertEqual(response.status_code, 200)


class DynamicStaticPageTests(TestCase):
    def test_existing_slug_returns_200(self):
        page = StaticPage.objects.create(
            title_uk="Тестова сторінка", slug="test-page", body="<p>x</p>"
        )
        response = self.client.get(f"/{page.slug}/")
        self.assertEqual(response.status_code, 200)

    def test_missing_slug_returns_404(self):
        response = self.client.get("/no-such-page/")
        self.assertEqual(response.status_code, 404)


class FaqViewTests(TestCase):
    def test_faq_page_returns_200_and_lists_items(self):
        category = FAQCategory.objects.create(name="Загальні", order=1)
        FAQItem.objects.create(category=category, question="Питання?", answer="Відповідь.", order=1)
        response = self.client.get("/faq/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Питання?")
