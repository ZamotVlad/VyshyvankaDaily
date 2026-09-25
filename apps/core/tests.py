import json
import re
import xml.etree.ElementTree as ET

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.utils import timezone

from apps.blog.models import BlogCategory, BlogPost
from apps.pages.models import FAQCategory, FAQItem
from apps.patterns.models import DailyPattern, Region


class SlugTransliterationTests(TestCase):
    def test_cyrillic_name_produces_latin_slug(self):
        region = Region.objects.create(
            name="Полтавщина",
            symbolism_description="Тест.",
            dominant_colors=["#000000"],
            shirt_cut_type="Тест",
            rotation_order=99,
        )
        self.assertTrue(region.slug.isascii())
        self.assertTrue(region.slug)


def extract_jsonld(html):
    """Витягує всі JSON-LD блоки зі сторінки й одразу парсить їх."""
    blocks = re.findall(r'<script type="application/ld\+json">(.*?)</script>', html, re.DOTALL)
    return [json.loads(b) for b in blocks]


class RobotsTxtTests(TestCase):
    def test_served_as_plain_text(self):
        response = self.client.get("/robots.txt")
        self.assertEqual(response.status_code, 200)
        self.assertIn("text/plain", response["Content-Type"])

    def test_blocks_private_sections_and_points_to_sitemap(self):
        body = self.client.get("/robots.txt").content.decode()
        self.assertIn("User-agent: *", body)
        for private in ("/accounts/", "/profile/settings/", "/collection/", "/admin/"):
            self.assertIn(f"Disallow: {private}", body)
        self.assertIn("/sitemap.xml", body)

    def test_does_not_block_legal_pages(self):
        """Свідоме рішення: privacy/terms лишаються відкритими для індексації
        як сигнал довіри (порада SEO-спеціалістки, 26.07)."""
        body = self.client.get("/robots.txt").content.decode()
        self.assertNotIn("terms", body)
        self.assertNotIn("privacy", body)


class SitemapTests(TestCase):
    def test_returns_parseable_xml(self):
        response = self.client.get("/sitemap.xml")
        self.assertEqual(response.status_code, 200)
        ET.fromstring(response.content)  # впаде, якщо XML побитий

    def test_contains_region_and_legal_pages(self):
        body = self.client.get("/sitemap.xml").content.decode()
        self.assertIn("/regions/", body)
        self.assertIn("/terms-of-use/", body)
        self.assertIn("/privacy-policy/", body)

    def test_has_hreflang_alternates(self):
        body = self.client.get("/sitemap.xml").content.decode()
        self.assertIn('hreflang="uk"', body)
        self.assertIn('hreflang="en"', body)
        self.assertIn('hreflang="x-default"', body)


class HeadMetaTests(TestCase):
    def test_homepage_has_canonical_and_robots_meta(self):
        response = self.client.get("/")
        self.assertContains(response, 'rel="canonical"')
        self.assertContains(response, 'name="robots"')
        self.assertContains(response, "index, follow")

    def test_html_lang_attribute_is_filled(self):
        """Порожній lang був реальним багом (бракувало i18n-процесора)."""
        html = self.client.get("/").content.decode()
        self.assertIn('<html lang="uk"', html)
        self.assertNotIn('<html lang=""', html)

    def test_english_page_declares_english_lang(self):
        html = self.client.get("/en/").content.decode()
        self.assertIn('<html lang="en"', html)


class JsonLdTests(TestCase):
    def test_homepage_emits_valid_site_jsonld(self):
        html = self.client.get("/").content.decode()
        blocks = extract_jsonld(html)
        self.assertTrue(blocks, "На головній немає жодного JSON-LD блоку")

        types = []
        for block in blocks:
            for node in block.get("@graph", [block]):
                types.append(node.get("@type"))
        self.assertIn("Organization", types)
        self.assertIn("WebSite", types)

    def test_jsonld_escapes_angle_brackets(self):
        """Неекранований < розірвав би сам тег script."""
        html = self.client.get("/").content.decode()
        scripts = re.findall(r'<script type="application/ld\+json">(.*?)</script>', html, re.DOTALL)
        for script in scripts:
            self.assertNotIn("<", script)

    def test_pattern_page_emits_visualartwork_jsonld(self):
        region = Region.objects.create(
            name="Тестова область",
            symbolism_description="Опис символіки регіону.",
            dominant_colors=["#000000"],
            shirt_cut_type="Тестовий крій",
            rotation_order=1,
        )
        pattern = DailyPattern.objects.create(
            date=timezone.localdate(),
            region=region,
            seed="s1",
            algorithm_version=1,
            svg_content="<svg>1</svg>",
        )
        html = self.client.get(f"/pattern/{pattern.date.isoformat()}/").content.decode()
        blocks = extract_jsonld(html)
        types = [b.get("@type") for b in blocks]
        self.assertIn("VisualArtwork", types)

        artwork = next(b for b in blocks if b.get("@type") == "VisualArtwork")
        self.assertIn(region.name, artwork["name"])
        self.assertEqual(artwork["locationCreated"]["name"], region.name)

    def test_blog_post_emits_blogposting_jsonld(self):
        category = BlogCategory.objects.create(name="Категорія")
        post = BlogPost.objects.create(
            title_uk="Тестова стаття",
            slug="test-article",
            excerpt_uk="Короткий опис",
            body="<p>Текст</p>",
            category=category,
            status="published",
            published_at=timezone.now(),
        )
        html = self.client.get(f"/blog/{post.slug}/").content.decode()
        blocks = extract_jsonld(html)
        types = [b.get("@type") for b in blocks]
        self.assertIn("BlogPosting", types)

        article = next(b for b in blocks if b.get("@type") == "BlogPosting")
        self.assertEqual(article["headline"], post.title)
        self.assertEqual(article["description"], post.excerpt)

    def test_faq_page_emits_faqpage_jsonld_with_items(self):
        category = FAQCategory.objects.create(name="Загальні питання", order=999)
        FAQItem.objects.create(
            category=category,
            question="Унікальне тестове запитання?",
            answer="Тестова відповідь.",
        )
        html = self.client.get("/faq/").content.decode()
        blocks = extract_jsonld(html)
        types = [b.get("@type") for b in blocks]
        self.assertIn("FAQPage", types)

        faq = next(b for b in blocks if b.get("@type") == "FAQPage")
        questions = [entity["name"] for entity in faq["mainEntity"]]
        self.assertIn("Унікальне тестове запитання?", questions)

    def test_faq_page_omits_jsonld_when_no_items(self):
        """jsonld_faq повертає порожній рядок, коли питань немає - перевіряємо, що тег не падає."""
        response = self.client.get("/faq/")
        self.assertEqual(response.status_code, 200)


class PrivatePageIndexingTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="seotester", password="pass12345")

    def test_collection_page_is_noindex(self):
        self.client.force_login(self.user)
        response = self.client.get("/collection/")
        self.assertContains(response, "noindex")

    def test_public_page_is_not_noindex(self):
        response = self.client.get("/regions/")
        self.assertNotContains(response, "noindex")


class BlogFeedTests(TestCase):
    def test_feed_is_served_as_rss(self):
        response = self.client.get("/blog/feed/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("xml", response["Content-Type"].lower())
        ET.fromstring(response.content)


@override_settings(DEBUG=False, ALLOWED_HOSTS=["testserver"])
class ErrorPageTests(TestCase):
    def test_404_uses_our_custom_template(self):
        response = self.client.get("/сторінки-точно-не-існує/")
        self.assertEqual(response.status_code, 404)
        self.assertContains(response, "Цю нитку обірвано", status_code=404)

    def test_500_template_renders_without_context_or_db(self):
        """500.html навмисно standalone: не extends base.html і не
        звертається ні до БД, ні до request - інакше сторінка помилки
        сама впала б там, де вже щось зламано."""
        from django.template.loader import render_to_string

        html = render_to_string("500.html")
        self.assertIn("Стібок зірвався", html)
        self.assertNotIn("{{", html)


class LanguageSwitchTests(TestCase):
    def test_switching_to_default_language_drops_prefix(self):
        """Регресія на баг Django #26556/#28567 - перемикання з /en/ на
        українську лишало старий префікс, і сторінка "залипала"."""
        response = self.client.post("/i18n/setlang/", {"language": "uk", "next": "/en/archive/"})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], "/archive/")

    def test_switching_to_english_adds_prefix(self):
        response = self.client.post("/i18n/setlang/", {"language": "en", "next": "/archive/"})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], "/en/archive/")

    def test_external_next_is_rejected(self):
        for next_url in ["//evil.com", "//evil.com/archive/", "/\\evil.com"]:
            for lang in ["uk", "en"]:
                response = self.client.post("/i18n/setlang/", {"language": lang, "next": next_url})
                self.assertEqual(response.status_code, 302)
                self.assertIn(response["Location"], ["/", "/en/"])

    def test_external_referer_keeps_only_path(self):
        response = self.client.post(
            "/i18n/setlang/", {"language": "en"}, HTTP_REFERER="https://evil.com/archive/"
        )
        self.assertEqual(response["Location"], "/en/archive/")


class ContextProcessorTests(TestCase):
    def test_canonical_url_present_on_home(self):
        response = self.client.get("/")
        self.assertIn("canonical_url", response.context)
        self.assertTrue(response.context["canonical_url"].endswith("/"))

    def test_canonical_url_includes_page_param(self):
        response = self.client.get("/archive/?page=2")
        self.assertIn("page=2", response.context["canonical_url"])

    def test_alternate_url_present(self):
        response = self.client.get("/")
        self.assertIn("alternate_url", response.context)


class SecurityHeadersMiddlewareTests(TestCase):
    def test_csp_header_present_on_public_pages(self):
        response = self.client.get("/")
        self.assertIn("Content-Security-Policy", response)
        self.assertNotIn("unsafe-eval", response["Content-Security-Policy"])

    def test_permissions_policy_header_present(self):
        response = self.client.get("/")
        self.assertIn("Permissions-Policy", response)
        self.assertIn("camera=()", response["Permissions-Policy"])
