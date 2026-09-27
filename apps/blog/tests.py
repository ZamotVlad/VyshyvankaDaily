from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.management import call_command
from django.test import TestCase, override_settings
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

    def test_page_views_do_not_count_towards_limit(self):
        for _ in range(5):
            self.client.get("/blog/propose/")
        response = self.client.post("/blog/propose/", self._valid_data())
        self.assertEqual(response.status_code, 302)

    def test_limit_is_per_client_ip_behind_proxy(self):
        for i in range(3):
            data = {**self._valid_data(), "email": f"a{i}@example.com"}
            self.client.post("/blog/propose/", data, HTTP_X_FORWARDED_FOR="1.1.1.1")
        data = {**self._valid_data(), "email": "b@example.com"}
        response = self.client.post("/blog/propose/", data, HTTP_X_FORWARDED_FOR="2.2.2.2")
        self.assertEqual(response.status_code, 302)

    def test_submitter_ip_is_last_forwarded_address(self):
        self.client.post(
            "/blog/propose/", self._valid_data(), HTTP_X_FORWARDED_FOR="6.6.6.6, 3.3.3.3"
        )
        self.assertEqual(GuestPostSubmission.objects.get().submitter_ip, "3.3.3.3")


@override_settings(
    CACHES={
        "default": {
            "BACKEND": "django.core.cache.backends.db.DatabaseCache",
            "LOCATION": "django_cache",
        }
    }
)
class GuestPostDatabaseCacheTests(GuestPostSubmissionTests):
    def setUp(self):
        call_command("createcachetable", verbosity=0)
        super().setUp()


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
        self.assertNotContains(response, "Статті про цей регіон")

    def test_region_page_works_without_any_posts(self):
        response = self.client.get(f"/regions/{self.region.slug}/")
        self.assertEqual(response.status_code, 200)


class BlogDetailDraftAccessTests(TestCase):
    def setUp(self):
        self.category = BlogCategory.objects.create(name="Категорія")
        self.post = BlogPost.objects.create(
            title_uk="Чернетка",
            slug="draft-post",
            body="<p>x</p>",
            category=self.category,
            status="draft",
        )

    def test_anonymous_gets_404_on_draft(self):
        response = self.client.get(f"/blog/{self.post.slug}/")
        self.assertEqual(response.status_code, 404)

    def test_staff_can_view_draft(self):
        staff = get_user_model().objects.create_user(
            username="editor", password="pass12345", is_staff=True
        )
        self.client.force_login(staff)
        response = self.client.get(f"/blog/{self.post.slug}/")
        self.assertEqual(response.status_code, 200)


class BlogCategoryFilterTests(TestCase):
    def test_filter_by_category(self):
        cat_a = BlogCategory.objects.create(name="А", slug="a")
        cat_b = BlogCategory.objects.create(name="Б", slug="b")
        BlogPost.objects.create(
            title_uk="Пост А",
            slug="post-a",
            body="<p>x</p>",
            category=cat_a,
            status="published",
            published_at=timezone.now(),
        )
        BlogPost.objects.create(
            title_uk="Пост Б",
            slug="post-b",
            body="<p>x</p>",
            category=cat_b,
            status="published",
            published_at=timezone.now(),
        )
        response = self.client.get(f"/blog/?category={cat_a.slug}")
        titles = [p.title for p in response.context["page_obj"].object_list]
        self.assertIn("Пост А", titles)
        self.assertNotIn("Пост Б", titles)


class GuestPostProposeViewTests(TestCase):
    def test_get_returns_200(self):
        response = self.client.get("/blog/propose/")
        self.assertEqual(response.status_code, 200)

    def test_honeypot_filled_shows_success_without_saving(self):
        from apps.blog.models import GuestPostSubmission

        response = self.client.post(
            "/blog/propose/",
            {
                "author_name": "Бот",
                "author_email": "bot@example.com",
                "topic": "Тема",
                "honeypot": "заповнено",
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(GuestPostSubmission.objects.exists())


class BlogFeedTests(TestCase):
    def test_feed_returns_200_and_lists_published_post(self):
        category = BlogCategory.objects.create(name="Категорія")
        BlogPost.objects.create(
            title_uk="Стаття у стрічці",
            slug="feed-post",
            excerpt_uk="Опис",
            body="<p>x</p>",
            category=category,
            status="published",
            published_at=timezone.now(),
        )
        response = self.client.get("/blog/feed/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Стаття у стрічці")


class BlogAdminTests(TestCase):
    def test_status_badge_shows_published_color(self):
        from django.contrib import admin as django_admin

        from apps.blog.admin import BlogPostAdmin

        category = BlogCategory.objects.create(name="Категорія")
        post = BlogPost.objects.create(
            title_uk="Тест",
            slug="admin-test",
            body="<p>x</p>",
            category=category,
            status="published",
        )
        admin_instance = BlogPostAdmin(BlogPost, django_admin.site)
        badge = admin_instance.status_badge(post)
        self.assertIn("#3A7D2C", badge)

    def test_keyword_badge_shows_dash_when_empty(self):
        from django.contrib import admin as django_admin

        from apps.blog.admin import BlogPostAdmin

        category = BlogCategory.objects.create(name="Категорія")
        post = BlogPost.objects.create(
            title_uk="Тест 2",
            slug="admin-test-2",
            body="<p>x</p>",
            category=category,
        )
        admin_instance = BlogPostAdmin(BlogPost, django_admin.site)
        badge = admin_instance.keyword_badge(post)
        self.assertIn("—", badge)

    def test_category_post_count(self):
        from django.contrib import admin as django_admin

        from apps.blog.admin import BlogCategoryAdmin

        category = BlogCategory.objects.create(name="Категорія")
        BlogPost.objects.create(
            title_uk="Тест 3",
            slug="admin-test-3",
            body="<p>x</p>",
            category=category,
        )
        admin_instance = BlogCategoryAdmin(BlogCategory, django_admin.site)
        self.assertEqual(admin_instance.post_count(category), 1)


class BlogCoverAltTests(TestCase):
    def test_cover_alt_is_own_field_not_title(self):
        category = BlogCategory.objects.create(name_uk="Техніки", slug="tech", is_active=True)
        post = BlogPost.objects.create(
            category=category,
            title_uk="Символіка Полтавщини",
            slug="cover-alt",
            excerpt_uk="Опис",
            body="<p>Текст</p>",
            cover_image_url="https://example.com/sorochka.webp",
            cover_image_alt_uk="Сорочка з Полтавщини, біла гладь",
            status="published",
            published_at=timezone.now(),
        )
        for url in ("/blog/", f"/blog/{post.slug}/"):
            html = self.client.get(url).content.decode()
            self.assertIn('alt="Сорочка з Полтавщини, біла гладь"', html)
            self.assertNotIn('alt="Символіка Полтавщини"', html)


class BlogEnglishBodyTests(TestCase):
    def setUp(self):
        self.category = BlogCategory.objects.create(name_uk="Стиль", slug="style", is_active=True)

    def _post(self, slug, body_en=""):
        return BlogPost.objects.create(
            category=self.category,
            title_uk="Стаття",
            title_en="Article",
            slug=slug,
            excerpt_uk="Опис",
            body="<p>Український текст</p>",
            body_en=body_en,
            status="published",
            published_at=timezone.now(),
        )

    def test_en_page_shows_english_body_and_is_indexable(self):
        post = self._post("with-en", "<p>English text</p>")
        html = self.client.get(f"/en/blog/{post.slug}/").content.decode()
        self.assertIn("English text", html)
        self.assertNotIn("Український текст", html)
        self.assertIn('content="index, follow"', html)

    def test_en_page_without_english_is_noindex(self):
        post = self._post("no-en")
        html = self.client.get(f"/en/blog/{post.slug}/").content.decode()
        self.assertIn('content="noindex, follow"', html)
        uk_html = self.client.get(f"/blog/{post.slug}/").content.decode()
        self.assertIn('content="index, follow"', uk_html)

    def test_sitemap_lists_en_only_with_english(self):
        self._post("with-en", "<p>English</p>")
        self._post("no-en")
        body = self.client.get("/sitemap.xml").content.decode()
        self.assertIn("/en/blog/with-en/", body)
        self.assertNotIn("/en/blog/no-en/", body)
        self.assertIn("/blog/no-en/", body)

    def test_figures_survive_sanitizing(self):
        post = self._post(
            "figs",
            '<figure class="vd-figure--pair"><img src="/static/a.webp" alt="Опис" '
            'width="10" height="10" loading="lazy" onerror="x()"><figcaption>Фото</figcaption>'
            '</figure><aside class="vd-callout"><p>Факт</p></aside>',
        )
        post.refresh_from_db()
        self.assertIn('<figure class="vd-figure--pair">', post.body_en)
        self.assertIn('alt="Опис"', post.body_en)
        self.assertIn("<figcaption>Фото</figcaption>", post.body_en)
        self.assertIn('<aside class="vd-callout">', post.body_en)
        self.assertNotIn("onerror", post.body_en)


class LoadBlogPostsCommandTests(TestCase):
    def setUp(self):
        from apps.blog.models import Author

        Author.objects.create(name_uk="Владислав Замотайло", name_en="Vladyslav Zamotailo")

    def test_article_file_loads_and_is_idempotent(self):
        import io

        call_command("load_blog_posts", "blog_posts.json", stdout=io.StringIO())
        call_command("load_blog_posts", "blog_posts.json", stdout=io.StringIO())
        post = BlogPost.objects.get(slug="z-chym-nosyty-vyshyvanku")
        self.assertEqual(BlogPost.objects.count(), 1)
        self.assertEqual(post.status, "published")
        self.assertIsNotNone(post.published_at)
        self.assertEqual(post.blog_author.name_uk, "Владислав Замотайло")
        self.assertTrue(post.has_english)
        for body in (post.body, post.body_en):
            self.assertNotIn("—", body)
            self.assertNotIn("instagram.com/liliia.rebrik</a>", body)
            self.assertIn("<figure>", body)
        self.assertIn('href="/regions/poltavska-oblast/"', post.body)
        self.assertIn('href="/en/regions/poltavska-oblast/"', post.body_en)

    def test_article_images_exist(self):
        import json
        import re
        from pathlib import Path

        from django.conf import settings

        entry = json.loads(Path("blog_posts.json").read_text(encoding="utf-8"))[0]
        paths = set(re.findall(r'src="/static/([^"]+)"', entry["uk"]["body"] + entry["en"]["body"]))
        paths.add(entry["cover_image_url"].split("/static/", 1)[1])
        for path in paths:
            self.assertTrue((Path(settings.BASE_DIR) / "static" / path).exists(), path)

    def test_dry_run_saves_nothing(self):
        import io

        call_command("load_blog_posts", "blog_posts.json", "--dry-run", stdout=io.StringIO())
        self.assertFalse(BlogPost.objects.exists())
        self.assertFalse(BlogCategory.objects.filter(slug="styling").exists())


class FirstArticleSeoTests(TestCase):
    def setUp(self):
        import io

        from apps.blog.models import Author

        Author.objects.create(name_uk="Владислав Замотайло", name_en="Vladyslav Zamotailo")
        call_command("load_blog_posts", "blog_posts.json", stdout=io.StringIO())
        self.post = BlogPost.objects.get(slug="z-chym-nosyty-vyshyvanku")

    def test_seo_title_differs_from_h1_in_both_languages(self):
        for lang in ("uk", "en"):
            title = getattr(self.post, f"title_{lang}")
            seo_title = getattr(self.post, f"seo_title_{lang}")
            self.assertTrue(seo_title)
            self.assertNotIn(seo_title.split(":")[0], title)

    def test_author_meta_is_article_author(self):
        html = self.client.get(f"/blog/{self.post.slug}/").content.decode()
        self.assertIn('<meta name="author" content="Владислав Замотайло">', html)
        html = self.client.get(f"/en/blog/{self.post.slug}/").content.decode()
        self.assertIn('<meta name="author" content="Vladyslav Zamotailo">', html)

    def test_only_museum_and_fashion_week_links_are_external(self):
        import re

        for body in (self.post.body, self.post.body_en):
            external = re.findall(r'<a href="(https?://[^"]+)"([^>]*)>', body)
            hosts = {re.sub(r"https?://([^/]+)/.*", r"\1", href) for href, _ in external}
            self.assertEqual(hosts, {"museum.mincult.gov.ua", "fashionweek.ua"})
            for _, attrs in external:
                self.assertIn('rel="noopener"', attrs)
            self.assertNotIn('href="https://www.instagram.com', body)
            self.assertNotIn('href="http://instagram.com', body)
