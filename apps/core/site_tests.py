import re
from datetime import date
from io import StringIO
from pathlib import Path

from django.conf import settings
from django.contrib.staticfiles import finders
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.utils import translation

from apps.core.llms import html_to_markdown
from apps.core.templatetags.assets_tags import hash_static_srcs, local_static
from apps.core.templatetags.seo_tags import brand_title
from apps.patterns.models import DailyPattern, Region
from apps.patterns.services.symbols import stitch_svg


class HtmlToMarkdownTests(TestCase):
    def test_blocks_lists_and_images(self):
        md = html_to_markdown(
            "<h2>Розділ</h2><p>Абзац<br>далі</p><ul><li>Один</li><li>Два</li></ul>"
            '<blockquote>Цитата</blockquote><img src="x.webp" alt="Сорочка">'
            "<script>alert(1)</script><style>p{}</style>"
        )
        self.assertIn("### Розділ", md)
        self.assertIn("Абзац далі", md)
        self.assertIn("- Один\n\n- Два", md)
        self.assertIn("> Цитата", md)
        self.assertIn("[Зображення: Сорочка]", md)
        self.assertNotIn("alert", md)
        self.assertNotIn("p{}", md)

    def test_table_becomes_markdown_table(self):
        md = html_to_markdown(
            "<table><tr><th>Вид</th><th>Де</th></tr><tr><td>Уставкова</td><td>Волинь</td></tr>"
            "<tr><td></td><td></td></tr></table>"
        )
        self.assertEqual(md, "| Вид | Де |\n| --- | --- |\n| Уставкова | Волинь |")

    def test_entities_and_empty_input(self):
        self.assertEqual(html_to_markdown("<p>A &amp; B</p>"), "A & B")
        self.assertEqual(html_to_markdown(None), "")


class SeedDevDataTests(TestCase):
    def test_command_is_idempotent_and_site_renders(self):
        call_command("seed_dev_data", stdout=StringIO())
        call_command("seed_dev_data", stdout=StringIO())
        self.assertEqual(Region.objects.filter(name="Тестовий регіон").count(), 1)
        self.assertEqual(self.client.get("/").status_code, 200)


class StaticAssetUrlTests(TestCase):
    @override_settings(
        STORAGES={
            **settings.STORAGES,
            "staticfiles": {
                "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
            },
        }
    )
    def test_own_static_urls_become_static_urls(self):
        self.assertEqual(
            local_static("https://vyshyvankadaily.live/static/blog/a.webp"), "/static/blog/a.webp"
        )
        self.assertEqual(local_static("/static/blog/a.webp"), "/static/blog/a.webp")
        self.assertEqual(
            local_static("https://upload.wikimedia.org/x.jpg"), "https://upload.wikimedia.org/x.jpg"
        )
        self.assertEqual(local_static(""), "")
        html = hash_static_srcs(
            '<img src="https://vyshyvankadaily.live/static/blog/a.webp" alt="">'
        )
        self.assertEqual(html, '<img src="/static/blog/a.webp" alt="">')

    def test_small_variant_used_when_present(self):
        url = local_static("/static/authors/vladyslav-zamotailo-author.webp", "64")
        self.assertIn("vladyslav-zamotailo-author-64", url)
        url = local_static("/static/authors/vladyslav-zamotailo-author.webp", "999")
        self.assertNotIn("-999", url)

    def test_blog_images_stay_under_100_kb(self):
        root = Path(finders.find("blog"))
        for path in root.rglob("*.webp"):
            with self.subTest(path=path.name):
                self.assertLessEqual(path.stat().st_size, 100 * 1024)


class TitleAndMetaTests(TestCase):
    def test_brand_suffix_only_when_title_fits(self):
        self.assertEqual(brand_title("Блог"), "Блог - VyshyvankaDaily")
        long = "Odesa Vyshyvanka: Embroidery Ornament of the Odesa Region"
        self.assertEqual(brand_title(long), long)

    def test_pattern_page_has_own_description_and_readable_date(self):
        region = Region.objects.create(
            name="Тестова область",
            symbolism_description="<p>Опис <b>символіки</b>.</p>",
            seo_description="Вишиванки тестової області: мотиви й кольори.",
            dominant_colors=["#000000"],
            rotation_order=1,
            verification_status=Region.VerificationStatus.VERIFIED,
        )
        pattern = DailyPattern.objects.create(
            date=date(2026, 10, 1),
            region=region,
            seed="2026-10-01",
            algorithm_version=2,
            svg_content="<svg></svg>",
        )
        with translation.override("uk"):
            self.assertEqual(pattern.breadcrumbs[-1]["label"], "1 жовтня 2026")
        html = self.client.get("/pattern/2026-10-01/").content.decode()
        desc = re.search(r'<meta name="description" content="([^"]*)"', html)[1]
        self.assertTrue(desc.startswith("Орнамент дня 1 жовтня 2026: Тестова область."))
        self.assertLessEqual(len(desc), 155)
        self.assertNotIn("<b>", re.search(r'og:description" content="([^"]*)"', html)[1])


class TemplateDetailTests(TestCase):
    def test_footer_links_and_title(self):
        html = self.client.get("/about/").content.decode()
        footer = html[html.index("<footer") :]
        self.assertIn("Проєкт", footer)
        self.assertNotIn("Компанія", footer)
        self.assertIn('href="/regions/lvivska-oblast/"', footer)
        self.assertIn('href="/regions/"', footer)

    def test_svg_label_is_escaped(self):
        svg = stitch_svg(["#"], label='Ромб "зірка"')
        self.assertIn('aria-label="Ромб &quot;зірка&quot;"', svg)

    def test_mobile_tables_and_checkbox_css(self):
        css = Path(finders.find("css/vd.css")).read_text(encoding="utf-8")
        self.assertRegex(
            css, r"@media \(max-width: 380px\) \{\s*\.vd-prose table \{\s*display: block;"
        )
        self.assertIn('.vd-form input[type="checkbox"]', css)

    def test_site_js_has_no_dead_language_select(self):
        js = Path(finders.find("js/site.js")).read_text(encoding="utf-8")
        self.assertNotIn(".vd-lang select", js)
        self.assertIn("parent.appendChild(el)", js)
        self.assertNotIn("layer.appendChild(r)", js)


class CollaborationPageTests(TestCase):
    def test_formats_listed_and_saved(self):
        from apps.blog.models import GuestPostSubmission

        html = self.client.get("/blog/propose/").content.decode()
        self.assertIn("Спонсорський матеріал", html)
        self.assertIn('name="collaboration_type"', html)
        self.client.post(
            "/blog/propose/",
            {
                "contact_name": "Бренд",
                "email": "brand@example.com",
                "brand_name": "Етнобренд",
                "collaboration_type": "sponsored",
                "proposed_topic": "Колекція сорочок",
                "proposal_description": "Хочемо розповісти про колекцію.",
                "honeypot": "",
            },
        )
        self.assertEqual(GuestPostSubmission.objects.get().collaboration_type, "sponsored")
        en = self.client.get("/en/blog/propose/").content.decode()
        self.assertIn("Ways to collaborate", en)
        self.assertIn("Turnkey article", en)
        self.assertIn('value="written_by_us"', html)


class ProposalLengthTests(TestCase):
    def setUp(self):
        from django.core.cache import cache

        cache.clear()

    def _post(self, text):
        return self.client.post(
            "/blog/propose/",
            {
                "contact_name": "Автор",
                "email": "a@example.com",
                "proposed_topic": "Тема",
                "proposal_description": text,
                "honeypot": "",
            },
        )

    def test_description_limited_to_500_chars(self):
        from apps.blog.models import GuestPostSubmission

        html = self.client.get("/blog/propose/").content.decode()
        self.assertIn('maxlength="500"', html)
        self.assertIn("До 500 символів.", html)
        response = self._post("я" * 501)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(GuestPostSubmission.objects.exists())
        self.assertEqual(self._post("я" * 500).status_code, 302)
        self.assertEqual(GuestPostSubmission.objects.count(), 1)
        self.assertIn(
            "Up to 500 characters.", self.client.get("/en/blog/propose/").content.decode()
        )

    def test_textarea_cannot_grow_endlessly(self):
        css = Path(finders.find("css/vd.css")).read_text(encoding="utf-8")
        self.assertIn("max-height: 22em;", css)


class PatternPagesNoindexTests(TestCase):
    def test_every_pattern_page_is_noindex_in_both_languages_and_not_in_sitemap(self):
        from django.utils import timezone

        region = Region.objects.create(
            name="Тестова область",
            symbolism_description="<p>Опис.</p>",
            dominant_colors=["#000000"],
            rotation_order=1,
            verification_status=Region.VerificationStatus.VERIFIED,
        )
        today = timezone.localdate()
        for d in (today, date(2026, 10, 1)):
            DailyPattern.objects.create(
                date=d,
                region=region,
                seed=d.isoformat(),
                algorithm_version=2,
                svg_content="<svg></svg>",
            )
            for prefix in ("", "/en"):
                with self.subTest(day=d, lang=prefix or "uk"):
                    html = self.client.get(f"{prefix}/pattern/{d.isoformat()}/").content.decode()
                    self.assertIn('<meta name="robots" content="noindex, follow">', html)
                    self.assertNotIn('<link rel="alternate" hreflang', html)
        self.assertNotIn("/pattern/", self.client.get("/sitemap.xml").content.decode())


class SnippetLengthTests(TestCase):
    """Межі, у які вкладаються сніпети в пошуку (кирилиця ширша за латиницю)."""

    def test_region_titles_and_descriptions_fit_search_snippets(self):
        import json

        for r in json.loads(Path(settings.BASE_DIR, "region_content.json").read_text("utf-8")):
            with self.subTest(region=r["slug"]):
                self.assertLessEqual(len(r["seo_title"]), 55)
                self.assertLessEqual(len(r["seo_description"]), 140)
                self.assertLessEqual(len(r["en"]["seo_title"]), 60)
                self.assertLessEqual(len(r["en"]["seo_description"]), 155)
                words = r["seo_title"].split()[1:]
                capitalized = [w for w in words if len(w) > 3 and w[0].isupper()]
                proper = {"Полтавщини", "Києва", "Тернополя", "Тернопільщини", "Запоріжжя"}
                self.assertLessEqual(len([w for w in capitalized if w not in proper]), 2)

    def test_brand_suffix_respects_cyrillic_limit(self):
        self.assertEqual(brand_title("Часті запитання"), "Часті запитання - VyshyvankaDaily")
        long_uk = "Вишиванки по регіонах України: орнаменти всіх областей"
        self.assertEqual(brand_title(long_uk), long_uk)
        self.assertEqual(
            brand_title("Про нас: як створюється VyshyvankaDaily"),
            "Про нас: як створюється VyshyvankaDaily",
        )


class CrawlHygieneTests(TestCase):
    def setUp(self):
        from django.core.cache import cache

        cache.clear()

    def test_login_links_are_nofollow(self):
        html = self.client.get("/regions/").content.decode()
        links = re.findall(r'<a [^>]*href="/accounts/(?:login|signup)/[^"]*"[^>]*>', html)
        self.assertTrue(links)
        for link in links:
            with self.subTest(link=link):
                self.assertIn('rel="nofollow"', link)

    def test_map_links_have_text_and_indexable_pages_keep_hreflang(self):
        html = self.client.get("/regions/").content.decode()
        self.assertEqual(html.count('<text class="vd-map__name">'), html.count('class="vd-map__rg'))
        self.assertIn('<text class="vd-map__name">Полтавська область</text>', html)
        self.assertIn('<link rel="alternate" hreflang="en"', html)

    def test_home_title_differs_from_h1(self):
        html = self.client.get("/").content.decode()
        title = re.search(r"<title>(.*?)</title>", html, re.S).group(1).strip()
        h1 = re.search(r"<h1[^>]*>(.*?)</h1>", html, re.S).group(1).strip()
        self.assertNotEqual(title, h1)
        self.assertIn(h1.lower(), title.lower())
