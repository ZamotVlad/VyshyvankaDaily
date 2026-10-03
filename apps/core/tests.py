import json
import re
import xml.etree.ElementTree as ET
from unittest import skipUnless

from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.utils import timezone

from apps.blog.models import BlogCategory, BlogPost
from apps.pages.models import FAQCategory, FAQItem
from apps.patterns.models import DailyPattern, Region, Source


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

    def test_blocks_english_versions_of_private_sections(self):
        body = self.client.get("/robots.txt").content.decode()
        for private in ("/en/accounts/", "/en/profile/settings/", "/en/collection/"):
            self.assertIn(f"Disallow: {private}", body)

    def test_blocks_blog_filters_but_not_blog(self):
        body = self.client.get("/robots.txt").content.decode()
        for prefix in ("", "/en"):
            self.assertIn(f"Disallow: {prefix}/blog/?category=", body)
            self.assertIn(f"Disallow: {prefix}/blog/?q=", body)
        self.assertNotIn("Disallow: /blog/\n", body)

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

    def test_contains_author_pages(self):
        from apps.blog.models import Author

        author = Author.objects.create(name="Тест Автор")
        body = self.client.get("/sitemap.xml").content.decode()
        self.assertIn(f"/blog/author/{author.slug}/", body)

    def test_has_hreflang_alternates(self):
        body = self.client.get("/sitemap.xml").content.decode()
        self.assertIn('hreflang="uk"', body)
        self.assertIn('hreflang="en"', body)
        self.assertIn('hreflang="x-default"', body)


class OpenGraphTests(TestCase):
    def test_common_og_tags_on_every_page(self):
        body = self.client.get("/archive/").content.decode()
        self.assertIn('<meta property="og:url" content="http://testserver/archive/">', body)
        self.assertIn('<meta property="og:site_name" content="VyshyvankaDaily">', body)
        self.assertIn('<meta property="og:locale" content="uk_UA">', body)
        self.assertIn('<meta name="twitter:card" content="summary_large_image">', body)

    def test_og_locale_follows_language(self):
        body = self.client.get("/en/archive/").content.decode()
        self.assertIn('<meta property="og:locale" content="en_US">', body)
        self.assertIn('<meta property="og:locale:alternate" content="uk_UA">', body)


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

    def test_pattern_page_emits_imageobject_jsonld(self):
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
        iso = pattern.date.isoformat()
        html = self.client.get(f"/pattern/{iso}/").content.decode()
        blocks = extract_jsonld(html)
        types = [b.get("@type") for b in blocks]
        self.assertIn("ImageObject", types)
        self.assertNotIn("VisualArtwork", types)

        image = next(b for b in blocks if b.get("@type") == "ImageObject")
        self.assertIn(region.name, image["name"])
        self.assertTrue(image["contentUrl"].endswith(f"/pattern/{iso}.svg"))
        self.assertEqual(image["encodingFormat"], "image/svg+xml")
        self.assertEqual(image["contentLocation"]["name"], region.name)

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
        self.assertEqual(article["mainEntityOfPage"]["@id"], article["url"])
        self.assertIn("logo", article["publisher"])
        self.assertGreater(article["wordCount"], 0)

    def test_region_page_emits_article_with_citations(self):
        region = Region.objects.create(
            name="Тестова область",
            symbolism_description="<p>Опис символіки регіону.</p>",
            seo_title="Тестовий заголовок",
            seo_description="Тестовий опис.",
            dominant_colors=["#000000"],
            shirt_cut_type="Тестовий крій",
            rotation_order=1,
        )
        source = Source.objects.create(
            name="Тестовий каталог",
            source_type="museum",
            author_or_institution="Тестовий музей",
            reference="Тест.",
            publication_year=2013,
        )
        region.sources.add(source)
        html = self.client.get(f"/regions/{region.slug}/").content.decode()
        blocks = extract_jsonld(html)
        article = next(b for b in blocks if b.get("@type") == "Article")
        self.assertEqual(article["headline"], "Тестовий заголовок")
        self.assertEqual(article["description"], "Тестовий опис.")
        self.assertEqual(article["about"]["name"], region.name)
        self.assertEqual(article["citation"][0]["name"], "Тестовий каталог")
        self.assertEqual(article["citation"][0]["author"]["@type"], "Organization")
        self.assertEqual(article["citation"][0]["datePublished"], "2013")

    def test_organization_has_logo_and_email(self):
        html = self.client.get("/").content.decode()
        org = next(
            node
            for block in extract_jsonld(html)
            for node in block.get("@graph", [block])
            if node.get("@type") == "Organization"
        )
        self.assertTrue(org["logo"]["url"].endswith(".png"))
        self.assertEqual(org["email"], "vyshyvankadaily@gmail.com")
        self.assertIn("https://ko-fi.com/vyshyvankadaily", org["sameAs"])

    def test_faq_page_has_no_faqpage_jsonld(self):
        category = FAQCategory.objects.create(name="Загальні питання", order=999)
        FAQItem.objects.create(
            category=category,
            question="Унікальне тестове запитання?",
            answer="Тестова відповідь.",
        )
        response = self.client.get("/faq/")
        self.assertEqual(response.status_code, 200)
        types = [b.get("@type") for b in extract_jsonld(response.content.decode())]
        self.assertNotIn("FAQPage", types)


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

    def test_head_hreflang_lists_both_languages_and_x_default(self):
        for path in ["/archive/", "/en/archive/"]:
            body = self.client.get(path).content.decode()
            self.assertIn('hreflang="uk" href="http://testserver/archive/"', body)
            self.assertIn('hreflang="en" href="http://testserver/en/archive/"', body)
            self.assertIn('hreflang="x-default" href="http://testserver/archive/"', body)

    def test_canonical_ignores_invalid_or_first_page_param(self):
        for query in ["?page=abc", "?page=1", "?page=-3", "?page=0"]:
            response = self.client.get(f"/archive/{query}")
            self.assertEqual(response.context["canonical_url"], "http://testserver/archive/")


class SecurityHeadersMiddlewareTests(TestCase):
    def test_csp_header_present_on_public_pages(self):
        response = self.client.get("/")
        self.assertIn("Content-Security-Policy", response)
        self.assertNotIn("unsafe-eval", response["Content-Security-Policy"])

    def test_permissions_policy_header_present(self):
        response = self.client.get("/")
        self.assertIn("Permissions-Policy", response)
        self.assertIn("camera=()", response["Permissions-Policy"])

    def test_csp_does_not_allow_unused_third_party_scripts(self):
        for path in ["/", "/vd/login/"]:
            self.assertNotIn("cloudflareinsights", self.client.get(path)["Content-Security-Policy"])

    def test_public_pages_use_self_hosted_fonts_only(self):
        response = self.client.get("/")
        csp = response["Content-Security-Policy"]
        self.assertNotIn("googleapis", csp)
        self.assertIn("font-src 'self';", csp)
        html = response.content.decode()
        self.assertNotIn("fonts.googleapis.com", html)
        self.assertRegex(html, r"@font-face \{ font-family: \"Unbounded\";")
        self.assertIn("fonts/unbounded-cyrillic.woff2", html)
        en = self.client.get("/en/").content.decode()
        self.assertIn("fonts/unbounded-latin.woff2", en)

    def test_admin_keeps_google_fonts_for_its_theme(self):
        csp = self.client.get("/vd/login/")["Content-Security-Policy"]
        self.assertIn("https://fonts.gstatic.com", csp)

    def test_scripts_are_deferred_and_touch_icon_linked(self):
        html = self.client.get("/").content.decode()
        self.assertIn('bootstrap.bundle.min.js" defer>', html)
        self.assertIn('js/site.js" defer>', html)
        self.assertIn('rel="apple-touch-icon"', html)

    def test_font_files_are_served(self):
        for name in ("unbounded-cyrillic.woff2", "ptserif-400-latin.woff2"):
            self.assertEqual(self.client.get(f"/static/fonts/{name}").status_code, 200)

    def test_html_is_gzip_compressed_when_client_accepts_it(self):
        plain = self.client.get("/regions/")
        compressed = self.client.get("/regions/", HTTP_ACCEPT_ENCODING="gzip")
        self.assertEqual(compressed["Content-Encoding"], "gzip")
        self.assertIn("Accept-Encoding", compressed["Vary"])
        self.assertLess(len(compressed.content), len(plain.content) / 3)

    def test_static_files_get_security_headers(self):
        response = self.client.get("/static/css/vd.css")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["X-Content-Type-Options"], "nosniff")


@override_settings(ALLOWED_HOSTS=["vyshyvankadaily.live"], SECURE_SSL_REDIRECT=True)
class WwwRedirectMiddlewareTests(TestCase):
    def test_www_redirects_to_apex_keeping_path_and_query(self):
        response = self.client.get(
            "/en/archive/?region=x", HTTP_HOST="www.vyshyvankadaily.live", secure=True
        )
        self.assertEqual(response.status_code, 301)
        self.assertEqual(response["Location"], "https://vyshyvankadaily.live/en/archive/?region=x")

    def test_plain_http_www_goes_straight_to_https_apex(self):
        response = self.client.get("/", HTTP_HOST="www.vyshyvankadaily.live")
        self.assertEqual(response["Location"], "https://vyshyvankadaily.live/")

    def test_unknown_www_host_is_rejected(self):
        response = self.client.get("/", HTTP_HOST="www.evil.com", secure=True)
        self.assertEqual(response.status_code, 400)

    def test_apex_is_served_normally(self):
        response = self.client.get("/robots.txt", HTTP_HOST="vyshyvankadaily.live", secure=True)
        self.assertEqual(response.status_code, 200)


@override_settings(
    ALLOWED_HOSTS=["vyshyvankadaily.live", "app-123.herokuapp.com"],
    CANONICAL_HOST="vyshyvankadaily.live",
    SECURE_SSL_REDIRECT=True,
)
class HerokuAppRedirectTests(TestCase):
    def test_herokuapp_redirects_to_canonical_host(self):
        response = self.client.get("/regions/?a=1", HTTP_HOST="app-123.herokuapp.com", secure=True)
        self.assertEqual(response.status_code, 301)
        self.assertEqual(response["Location"], "https://vyshyvankadaily.live/regions/?a=1")

    @override_settings(CANONICAL_HOST="")
    def test_no_redirect_without_canonical_host(self):
        response = self.client.get("/robots.txt", HTTP_HOST="app-123.herokuapp.com", secure=True)
        self.assertEqual(response.status_code, 200)


class SecurityTxtTests(TestCase):
    def test_security_txt_has_contact_and_future_expiry(self):
        from datetime import datetime

        response = self.client.get("/.well-known/security.txt")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/plain")
        body = response.content.decode()
        self.assertIn("Contact: mailto:vyshyvankadaily@gmail.com", body)
        expires = re.search(r"Expires: (\S+)", body).group(1)
        self.assertGreater(datetime.fromisoformat(expires), timezone.now())


class FaviconTests(TestCase):
    def test_favicon_ico_redirects_to_static_icon(self):
        response = self.client.get("/favicon.ico")
        self.assertEqual(response.status_code, 301)
        self.assertEqual(response["Location"], "/static/favicon/favicon.png")


class AdminLoginRateLimitTests(TestCase):
    def setUp(self):
        from django.core.cache import cache

        cache.clear()
        get_user_model().objects.create_superuser(
            username="boss", email="boss@example.com", password="right-pass-123"
        )

    def _login(self, password, ip="1.1.1.1"):
        return self.client.post(
            "/vd/login/",
            {"username": "boss", "password": password},
            HTTP_X_FORWARDED_FOR=ip,
        )

    def test_blocks_after_five_attempts_from_same_ip(self):
        for _ in range(5):
            self.assertEqual(self._login("wrong").status_code, 200)
        self.assertEqual(self._login("right-pass-123").status_code, 403)

    def test_other_ip_is_not_blocked(self):
        for _ in range(5):
            self._login("wrong")
        self.assertEqual(self._login("right-pass-123", ip="2.2.2.2").status_code, 302)

    def test_login_page_views_are_not_limited(self):
        for _ in range(10):
            self.assertEqual(self.client.get("/vd/login/").status_code, 200)


class AllauthClientIpTests(TestCase):
    @override_settings(ALLAUTH_TRUSTED_PROXY_COUNT=1)
    def test_allauth_uses_heroku_appended_ip(self):
        from allauth.core.internal.httpkit import get_client_ip
        from django.test import RequestFactory

        request = RequestFactory().get("/", HTTP_X_FORWARDED_FOR="6.6.6.6, 3.3.3.3")
        self.assertEqual(get_client_ip(request), "3.3.3.3")


EN_MO = settings.BASE_DIR / "locale" / "en" / "LC_MESSAGES" / "django.mo"


@skipUnless(EN_MO.exists(), "потрібен скомпільований django.mo (compilemessages)")
class EnglishUiStringsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        po = EN_MO.with_suffix(".po")
        if po.stat().st_mtime > EN_MO.stat().st_mtime:
            raise AssertionError("django.mo застарів: python manage.py compilemessages")

    def test_breadcrumbs_and_jsonld_are_translated(self):
        region = Region.objects.verified().first()
        body = self.client.get(f"/en/regions/{region.slug}/").content.decode()
        self.assertIn(">Regions</a>", body)
        self.assertIn('"name": "Home"', body)
        self.assertNotIn(">Регіони</a>", body)

    def test_save_message_is_translated(self):
        pattern = DailyPattern.objects.create(
            date=timezone.localdate().replace(day=1),
            region=Region.objects.first(),
            seed="s",
            algorithm_version=1,
            svg_content="<svg></svg>",
        )
        self.client.force_login(get_user_model().objects.create_user(username="e", password="p"))
        response = self.client.post(f"/en/pattern/{pattern.date}/save/", follow=True)
        self.assertContains(response, "Saved to collection.")


class BackupDataTests(TestCase):
    def _run_backup(self):
        import tempfile
        from io import StringIO
        from pathlib import Path

        from django.core.management import call_command

        tmp = Path(tempfile.mkdtemp())
        call_command("backup_data", output_dir=str(tmp), stdout=StringIO())
        return {p.name.split("_", 2)[-1]: p.read_text(encoding="utf-8") for p in tmp.iterdir()}

    def test_no_password_hashes_or_submitter_ips(self):
        from apps.blog.models import GuestPostSubmission

        user = get_user_model().objects.create_user(username="u", password="secret-pass-1")
        GuestPostSubmission.objects.create(
            contact_name="T", email="t@example.com", proposed_topic="T", submitter_ip="9.9.9.9"
        )
        files = self._run_backup()
        dump = "".join(files.values())
        self.assertNotIn(user.password, dump)
        self.assertNotIn("9.9.9.9", dump)
        self.assertIn('"username": "u"', files["users.json"])

    def test_includes_content_edited_in_admin(self):
        from apps.blog.models import Author

        Author.objects.create(name="Автор Бекапу")
        files = self._run_backup()
        self.assertIn("Автор Бекапу", files["content.json"])
        self.assertIn('"model": "patterns.region"', files["content.json"])


class AdminPagesRenderTests(TestCase):
    def test_changed_admin_pages_open(self):
        admin_user = get_user_model().objects.create_superuser(
            username="admin2", email="a@example.com", password="pass12345"
        )
        self.client.force_login(admin_user)
        for url in [
            "/vd/patterns/dailypattern/",
            "/vd/blog/blogpost/",
            "/vd/blog/blogpost/add/",
            "/vd/patterns/region/",
        ]:
            self.assertEqual(self.client.get(url).status_code, 200, url)


class TranslationSyncCommandTests(TestCase):
    def setUp(self):
        from django.utils import translation

        with translation.override("uk"):
            self.category = FAQCategory.objects.create(name="Тестова категорія", order=99)
            self.item = FAQItem.objects.create(
                category=self.category, question="Тестове питання?", answer="Відповідь."
            )

    def _call(self, name, *args):
        from io import StringIO

        from django.core.management import call_command

        out = StringIO()
        call_command(name, *args, stdout=out)
        return out.getvalue()

    def _file(self, entries):
        import tempfile

        f = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8")
        json.dump(entries, f, ensure_ascii=False)
        f.close()
        return f.name

    def _entry(self, question="Тестове питання?"):
        return {
            "model": "pages.faqitem",
            "uk": {"question": question, "answer": "Відповідь."},
            "en": {"question": "Test question?", "answer": "Answer."},
        }

    def test_export_is_ascii_json_with_both_languages(self):
        out = self._call("export_translations", "pages.faqitem")
        out.encode("ascii")
        entry = next(e for e in json.loads(out) if e["uk"]["question"] == "Тестове питання?")
        self.assertEqual(entry["en"], {"question": "", "answer": ""})

    def test_load_sets_english_when_ukrainian_matches(self):
        path = self._file([self._entry()])
        out = self._call("load_translations", path)
        self.item.refresh_from_db()
        self.assertEqual(self.item.question_en, "Test question?")
        self.assertEqual(self.item.question_uk, "Тестове питання?")
        self.assertIn("оновлено: 1", out)

    def test_check_and_dry_run_do_not_write(self):
        path = self._file([self._entry()])
        self.assertIn("Збіглося: 1", self._call("load_translations", path, "--check"))
        self._call("load_translations", path, "--dry-run")
        self.item.refresh_from_db()
        self.assertFalse(self.item.question_en)

    def test_changed_ukrainian_text_is_skipped_with_digest(self):
        from apps.core.translations import digest

        entry = self._entry()
        entry["uk"]["answer"] = "Стара відповідь."
        out = self._call("load_translations", self._file([entry]))
        self.item.refresh_from_db()
        self.assertFalse(self.item.question_en)
        self.assertIn(f"answer (база {digest('Відповідь.')})", out)
        self.assertIn("пропущено: 1", out)

    def test_repo_translations_file_is_valid(self):
        from pathlib import Path

        from apps.core.translations import TARGETS

        path = Path(settings.BASE_DIR) / "translations.json"
        for entry in json.loads(path.read_text(encoding="utf-8")):
            fields = set(TARGETS[entry["model"]])
            self.assertLessEqual(set(entry["uk"]), fields)
            self.assertEqual(set(entry["en"]), set(entry["uk"]))
            text = json.dumps(entry, ensure_ascii=False)
            self.assertNotIn("—", text)
            self.assertIsNone(re.search("[А-Яа-яІіЇїЄєҐґ]", "".join(entry["en"].values())))

    def test_author_created_in_english_gets_slug(self):
        from django.utils import translation

        from apps.blog.models import Author

        with translation.override("en"):
            author = Author.objects.create(name="Test Author")
        self.assertEqual(author.slug, "test-author")

    def test_faq_category_name_shows_in_english(self):
        self.category.name_en = "Test category"
        self.category.save()
        self.assertContains(self.client.get("/en/faq/"), "Test category")


class PurgedBootstrapTests(TestCase):
    def test_template_classes_kept_in_purged_bootstrap(self):
        from pathlib import Path

        base = Path(settings.BASE_DIR)
        vendor = base / "static" / "vendor" / "bootstrap"
        full = (vendor / "bootstrap.full.min.css").read_text(encoding="utf-8")
        purged = (vendor / "bootstrap.min.css").read_text(encoding="utf-8")
        sources = [*base.glob("templates/**/*.html"), *base.glob("apps/**/*.py")]
        classes = set()
        for path in sources:
            for attr in re.findall(r'class=["\']([^"\']*)', path.read_text(encoding="utf-8")):
                classes.update(t for t in attr.split() if re.fullmatch(r"[a-z][\w-]*", t))

        def has(css, cls):
            return re.search(r"\." + re.escape(cls) + r"(?![\w-])", css) is not None

        missing = sorted(c for c in classes if has(full, c) and not has(purged, c))
        self.assertEqual(missing, [], "Перезібрати Bootstrap: node tools/purge_bootstrap.cjs")


class SiteVersionTests(TestCase):
    def test_footer_shows_version_without_beta(self):
        html = self.client.get("/").content.decode()
        self.assertIn(f"v{settings.SITE_VERSION}", html)
        self.assertNotIn("Beta", html)


class LocalizedMetaTests(TestCase):
    PAGES = ["/", "/regions/", "/blog/", "/archive/", "/faq/", "/about/", "/contacts/"]

    def _meta(self, path):
        html = self.client.get(path).content.decode()
        title = re.search(r"<title>(.*?)</title>", html, re.S).group(1)
        desc = re.search(r'<meta name="description" content="([^"]*)"', html).group(1)
        return title + " " + desc

    def test_english_pages_have_english_title_and_description(self):
        for path in self.PAGES:
            meta = self._meta("/en" + path)
            self.assertIsNone(re.search("[А-Яа-яІіЇїЄєҐґ]", meta), f"/en{path}: {meta}")

    def test_ukrainian_pages_keep_ukrainian_meta(self):
        for path in self.PAGES:
            self.assertRegex(self._meta(path), "[А-Яа-яІіЇїЄєҐґ]", path)


class PageSpecificMetaTests(TestCase):
    def test_list_pages_have_their_own_description(self):
        default = "Щоденний генератор орнаменту української вишиванки"
        for path in ["/regions/", "/blog/", "/archive/", "/faq/"]:
            html = self.client.get(path).content.decode()
            desc = re.search(r'<meta name="description" content="([^"]*)"', html).group(1)
            self.assertNotIn(default, desc, path)
            self.assertLessEqual(len(desc), 160, path)
        self.assertContains(self.client.get("/regions/"), "<title>Вишиванки по регіонах України")


class TableOfContentsTests(TestCase):
    def test_build_toc_adds_unique_latin_ids(self):
        from apps.core.toc import build_toc

        html, items = build_toc(
            '<h2>Кольори: чому їх немає</h2><p>x</p><h2 class="a">Кольори: чому їх немає</h2>'
            "<h3>Не в змісті</h3><h2>Sources</h2>",
            reserved=("sources",),
        )
        self.assertEqual(
            [i["id"] for i in items],
            ["kolori-chomu-ikh-nemaie", "kolori-chomu-ikh-nemaie-2", "sources-2"],
        )
        self.assertIn('<h2 id="kolori-chomu-ikh-nemaie">', html)
        self.assertIn('<h2 id="kolori-chomu-ikh-nemaie-2" class="a">', html)
        self.assertNotIn("<h3 id", html)

    def test_region_page_has_toc_in_both_languages(self):
        from django.utils import translation

        from apps.patterns.models import Region

        with translation.override("uk"):
            region = Region.objects.create(
                name="Тестова область",
                slug="test-toc",
                symbolism_description="<h2>Перший розділ</h2><p>a</p><h2>Другий</h2><p>b</p>",
                symbolism_description_en="<h2>First part</h2><p>a</p><h2>Second</h2><p>b</p>",
                dominant_colors=["#000000"],
                rotation_order=901,
            )
        html = self.client.get(f"/regions/{region.slug}/").content.decode()
        self.assertIn('<h2 id="pershii-rozdil">', html)
        self.assertIn('href="#pershii-rozdil"', html)
        self.assertIn('href="#colors"', html)
        self.assertIn('id="colors"', html)
        self.assertIn('href="#ornaments"', html)
        self.assertIn("data-toc", html)
        en = self.client.get(f"/en/regions/{region.slug}/").content.decode()
        self.assertIn('<h2 id="first-part">', en)
        self.assertIn('href="#first-part"', en)
        self.assertIn(">Contents<", en)

    def test_single_heading_has_no_toc(self):
        from apps.blog.models import BlogCategory, BlogPost

        post = BlogPost.objects.create(
            category=BlogCategory.objects.create(name_uk="К", slug="k"),
            title_uk="Т",
            slug="one-h2",
            excerpt_uk="о",
            body="<h2>Один</h2><p>текст</p>",
            status="published",
            published_at=timezone.now(),
        )
        html = self.client.get(f"/blog/{post.slug}/").content.decode()
        self.assertIn('<h2 id="odin">', html)
        self.assertNotIn("data-toc", html)
        self.assertNotIn("vd-pagetoc--compact", html)


class AnalyticsAndAccessibilityTests(TestCase):
    def test_no_analytics_without_website_id(self):
        response = self.client.get("/")
        self.assertNotIn("umami", response.content.decode())
        self.assertNotIn("umami", response["Content-Security-Policy"])
        self.assertIn("script-src 'self';", response["Content-Security-Policy"])

    @override_settings(UMAMI_WEBSITE_ID="abc-123")
    def test_umami_script_and_csp_only_when_enabled(self):
        response = self.client.get("/")
        html = response.content.decode()
        self.assertIn('src="https://cloud.umami.is/script.js" data-website-id="abc-123"', html)
        csp = response["Content-Security-Policy"]
        self.assertIn("script-src 'self' https://cloud.umami.is", csp)
        self.assertIn("connect-src 'self' https://cloud.umami.is", csp)
        privacy = self.client.get("/privacy-policy/").content.decode()
        self.assertIn("Umami", privacy)
        self.assertNotIn("Sentry", privacy)

    def test_skip_link_and_back_to_top(self):
        html = self.client.get("/").content.decode()
        self.assertIn('class="vd-skip-link" href="#main-content"', html)
        self.assertIn('id="main-content"', html)
        self.assertIn("data-to-top", html)
        en = self.client.get("/en/").content.decode()
        self.assertIn("Skip to content", en)


class ArticleRegionLinkTests(TestCase):
    def setUp(self):
        from django.utils import translation

        from apps.blog.models import BlogCategory, BlogPost
        from apps.patterns.models import Region

        self.region = Region.objects.filter(slug="poltavska-oblast").first()
        if self.region is None:
            with translation.override("uk"):
                self.region = Region.objects.create(
                    name="Полтавська область",
                    slug="poltavska-oblast",
                    symbolism_description="<p>Текст</p>",
                    dominant_colors=["#FFFFFF", "#C9BFA9"],
                    rotation_order=902,
                )
        self.post = BlogPost.objects.create(
            category=BlogCategory.objects.create(name_uk="Стиль", slug="style"),
            title_uk="Стаття про стиль",
            slug="style-article",
            excerpt_uk="Опис",
            body='<h2>Розділ</h2><p><a href="/regions/poltavska-oblast/">полтавська</a></p>'
            '<img src="/static/blog/a.webp" alt="x">',
            body_en='<p><a href="/en/regions/poltavska-oblast/">Poltava</a></p>'
            '<img src="/static/blog/b.webp" alt="y">',
            cover_image_url="https://vyshyvankadaily.live/static/blog/cover.webp",
            status="published",
            published_at=timezone.now(),
        )

    def test_region_page_lists_article_that_links_to_it(self):
        html = self.client.get("/regions/poltavska-oblast/").content.decode()
        self.assertIn('href="/blog/style-article/"', html)
        self.assertIn('href="#articles"', html)

    def test_article_lists_mentioned_regions(self):
        html = self.client.get("/blog/style-article/").content.decode()
        self.assertIn('id="regions"', html)
        self.assertIn('href="/regions/poltavska-oblast/" class="vd-region-chip"', html)
        en = self.client.get("/en/blog/style-article/").content.decode()
        self.assertIn('href="/en/regions/poltavska-oblast/" class="vd-region-chip"', en)
        self.assertIn("Regions in this article", en)

    def test_sitemap_lists_article_images(self):
        body = self.client.get("/sitemap.xml").content.decode()
        self.assertIn('xmlns:image="http://www.google.com/schemas/sitemap-image/1.1"', body)
        self.assertIn(
            "<image:loc>https://vyshyvankadaily.live/static/blog/cover.webp</image:loc>", body
        )
        self.assertIn("<image:loc>http://example.com/static/blog/a.webp</image:loc>", body)
        self.assertIn("<image:loc>http://example.com/static/blog/b.webp</image:loc>", body)


class RegionImageSitemapTests(TestCase):
    def test_only_active_real_photos_and_no_ornaments(self):
        from apps.patterns.models import Region, RegionPhoto

        region = Region.objects.verified().first()
        body = self.client.get("/sitemap.xml").content.decode()
        self.assertNotIn(".svg</image:loc>", body)
        RegionPhoto.objects.create(
            region=region,
            thumbnail_url="https://example.org/t.webp",
            image_url="https://example.org/real-shirt.webp",
        )
        RegionPhoto.objects.create(
            region=region,
            thumbnail_url="https://example.org/t2.webp",
            image_url="https://example.org/hidden.webp",
            is_active=False,
        )
        body = self.client.get("/sitemap.xml").content.decode()
        self.assertIn("<image:loc>https://example.org/real-shirt.webp</image:loc>", body)
        self.assertNotIn("hidden.webp", body)
        self.assertNotIn("example.org/t.webp", body)
