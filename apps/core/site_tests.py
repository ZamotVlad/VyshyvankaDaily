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
