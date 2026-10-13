import re
from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from apps.blog.models import BlogCategory, BlogPost, GuestPostSubmission
from apps.pages.models import StaticPage
from apps.patterns.models import DailyPattern, Region, SavedPattern


class AdminUsabilityTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_superuser("admin", "a@example.com", "pass")
        self.client.force_login(self.user)
        self.region = Region.objects.create(
            name="Тестова область",
            symbolism_description="<p>Опис.</p>",
            dominant_colors=["#C23B2E"],
            rotation_order=1,
            verification_status=Region.VerificationStatus.VERIFIED,
        )
        self.pattern = DailyPattern.objects.create(
            date=date(2026, 10, 1),
            region=self.region,
            seed="2026-10-01",
            algorithm_version=2,
            svg_content="<svg></svg>",
        )

    def test_every_sidebar_link_opens(self):
        html = self.client.get(reverse("admin:index")).content.decode()
        links = set(re.findall(r'href="(?:http://testserver)?(/vd/[^"?]+/)"', html))
        self.assertGreater(len(links), 15)
        for link in links:
            with self.subTest(link=link):
                self.assertEqual(self.client.get(link).status_code, 200)

    def test_static_pages_and_saved_patterns_registered(self):
        page = StaticPage.objects.create(title="Сторінка", slug="storinka", body="<p>x</p>")
        saved = SavedPattern.objects.create(user=self.user, pattern=self.pattern)
        for url in (
            reverse("admin:pages_staticpage_change", args=[page.pk]),
            reverse("admin:patterns_savedpattern_change", args=[saved.pk]),
        ):
            self.assertEqual(self.client.get(url).status_code, 200)

    def test_daily_pattern_is_read_only_with_preview(self):
        url = reverse("admin:patterns_dailypattern_change", args=[self.pattern.pk])
        html = self.client.get(url).content.decode()
        self.assertIn('src="/pattern/2026-10-01.svg?v=', html)
        self.assertNotIn("&lt;svg", html)
        self.client.post(url, {"seed": "змінено", "algorithm_version": 9})
        self.pattern.refresh_from_db()
        self.assertEqual(self.pattern.seed, "2026-10-01")
        add = self.client.get(reverse("admin:patterns_dailypattern_add"))
        self.assertEqual(add.status_code, 403)

    def test_dashboard_cards_link_to_filtered_lists(self):
        GuestPostSubmission.objects.create(
            contact_name="Х", email="x@example.com", proposed_topic="Т", proposal_description="О"
        )
        html = self.client.get(reverse("admin:index")).content.decode()
        self.assertIn("guestpostsubmission/?review_status__exact=new", html)
        self.assertIn("dailypattern/?generation_status__exact=fallback", html)

    def test_list_pages_have_no_per_row_queries(self):
        for i in range(2, 8):
            Region.objects.create(
                name=f"Область {i}",
                symbolism_description="<p>x</p>",
                dominant_colors=["#000000"],
                rotation_order=i,
            )
        url = reverse("admin:patterns_region_changelist")
        with self.assertNumQueries(6):
            self.client.get(url)

    def test_labels_are_ukrainian(self):
        html = self.client.get(reverse("admin:patterns_region_changelist")).content.decode()
        self.assertIn("Порядок у ротації", html)
        self.assertNotIn("Rotation order", html)
        self.assertNotIn(">Patterns<", html)

    def test_blog_post_has_view_on_site_and_seo_counter(self):
        category = BlogCategory.objects.create(name="Гіди")
        post = BlogPost.objects.create(
            title_uk="Стаття", slug="stattia", body="<p>x</p>", excerpt_uk="Опис", category=category
        )
        html = self.client.get(
            reverse("admin:blog_blogpost_change", args=[post.pk])
        ).content.decode()
        self.assertIn("js/admin_seo_counter.js", html)
        self.assertIn("/r/", html)
        self.assertEqual(post.get_absolute_url(), "/blog/stattia/")

    def test_admin_theme_has_no_external_fonts(self):
        from django.contrib.staticfiles import finders

        css = open(finders.find("css/admin_theme.css"), encoding="utf-8").read()
        self.assertNotIn("googleapis", css)
        self.assertIn("fieldset.module", css)


class GuestPostBulkActionTests(TestCase):
    def test_bulk_reject(self):
        user = get_user_model().objects.create_superuser("admin", "a@example.com", "pass")
        self.client.force_login(user)
        sub = GuestPostSubmission.objects.create(
            contact_name="Бот",
            email="b@example.com",
            proposed_topic="Spam",
            proposal_description="x",
        )
        self.client.post(
            reverse("admin:blog_guestpostsubmission_changelist"),
            {"action": "mark_rejected", "_selected_action": [sub.pk]},
        )
        sub.refresh_from_db()
        self.assertEqual(sub.review_status, "rejected")


class ProfileFormLabelTests(TestCase):
    def test_labels_follow_language(self):
        user = get_user_model().objects.create_user("u", "u@example.com", "pass")
        self.client.force_login(user)
        uk = self.client.get("/profile/settings/").content.decode()
        en = self.client.get("/en/profile/settings/").content.decode()
        self.assertIn("Ім&#x27;я на сайті", uk)
        self.assertNotIn("Display name", uk)
        self.assertIn("Display name", en)
