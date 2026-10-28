import re
from datetime import date, timedelta
from io import StringIO
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.contrib.messages.storage.fallback import FallbackStorage
from django.template.loader import render_to_string
from django.test import RequestFactory, TestCase, override_settings
from django.utils import timezone

from apps.patterns.models import DailyPattern, Motif, Region, SavedPattern
from apps.patterns.services.generation import (
    NoFallbackAvailable,
    generate_daily_pattern,
    retry_fallback_pattern,
)
from apps.patterns.services.pattern_builder import build_svg_for_date
from apps.patterns.services.rotation import ROTATION_EPOCH, get_region_for_date
from apps.patterns.services.seed import get_rng


class SeedDeterminismTests(TestCase):
    def test_same_date_gives_same_sequence(self):
        rng1 = get_rng(date(2026, 7, 10))
        rng2 = get_rng(date(2026, 7, 10))
        self.assertEqual(
            [rng1.random() for _ in range(5)],
            [rng2.random() for _ in range(5)],
        )

    def test_different_dates_give_different_sequences(self):
        rng1 = get_rng(date(2026, 7, 10))
        rng2 = get_rng(date(2026, 7, 11))
        self.assertNotEqual(rng1.random(), rng2.random())


def make_region(name, rotation_order, is_active=True, verified=True):
    from django.utils import translation

    with translation.override("uk"):
        return _create_region(name, rotation_order, is_active, verified)


def _create_region(name, rotation_order, is_active, verified):
    return Region.objects.create(
        name=name,
        symbolism_description="Тестовий опис.",
        dominant_colors=["#000000"],
        shirt_cut_type="Тестовий крій",
        rotation_order=rotation_order,
        is_active=is_active,
        verification_status=(
            Region.VerificationStatus.VERIFIED if verified else Region.VerificationStatus.PENDING
        ),
    )


class RegionRotationTests(TestCase):
    def setUp(self):
        # Ізоляція від реальних 27 регіонів (Stage 5, міграції 0003-0005) —
        # без цього .verified() бачить усі активні регіони бази одночасно,
        # ламаючи розрахунок ротації, що прицільно розрахований на рівно
        # 2 тестові регіони.
        Region.objects.all().update(is_active=False)
        self.region_a = make_region("Регіон А", rotation_order=1)
        self.region_b = make_region("Регіон Б", rotation_order=2)

    def test_rotates_between_two_regions(self):
        first = get_region_for_date(ROTATION_EPOCH)
        second = get_region_for_date(ROTATION_EPOCH + timedelta(days=1))
        self.assertNotEqual(first, second)

    def test_cycles_back_after_full_rotation(self):
        first = get_region_for_date(ROTATION_EPOCH)
        after_cycle = get_region_for_date(ROTATION_EPOCH + timedelta(days=2))
        self.assertEqual(first, after_cycle)

    def test_deactivated_region_skipped(self):
        self.region_a.is_active = False
        self.region_a.save()
        result = get_region_for_date(ROTATION_EPOCH)
        self.assertEqual(result, self.region_b)

    def test_unverified_region_skipped(self):
        self.region_b.verification_status = Region.VerificationStatus.PENDING
        self.region_b.save()
        result = get_region_for_date(ROTATION_EPOCH + timedelta(days=1))
        self.assertEqual(result, self.region_a)


class RotationOrderTieTests(TestCase):
    def test_seeded_regions_have_unique_rotation_order(self):
        orders = list(Region.objects.values_list("rotation_order", flat=True))
        self.assertEqual(len(orders), len(set(orders)))

    def test_equal_rotation_order_falls_back_to_creation_order(self):
        Region.objects.all().update(is_active=False)
        first = make_region("Регіон Я", rotation_order=5)
        second = make_region("Регіон А", rotation_order=5)
        self.assertEqual(get_region_for_date(ROTATION_EPOCH), first)
        self.assertEqual(get_region_for_date(ROTATION_EPOCH + timedelta(days=1)), second)


def fake_success(pattern_date, region):
    return f"<svg>{pattern_date}-{region.pk}</svg>", []


def fake_failure(pattern_date, region):
    raise ValueError("Симуляція збою генерації")


class DailyPatternGenerationTests(TestCase):
    def setUp(self):
        self.region = make_region("Регіон А", rotation_order=1)

    def test_success_creates_pattern(self):
        pattern = generate_daily_pattern(ROTATION_EPOCH, 1, fake_success)
        self.assertEqual(pattern.generation_status, DailyPattern.GenerationStatus.SUCCESS)

    def test_repeat_call_returns_existing_not_regenerated(self):
        first = generate_daily_pattern(ROTATION_EPOCH, 1, fake_success)
        second = generate_daily_pattern(ROTATION_EPOCH, 1, fake_success)
        self.assertEqual(first.pk, second.pk)

    def test_fallback_used_on_exception(self):
        yesterday = ROTATION_EPOCH
        today = ROTATION_EPOCH + timedelta(days=1)
        generate_daily_pattern(yesterday, 1, fake_success)

        pattern = generate_daily_pattern(today, 2, fake_failure)

        self.assertEqual(pattern.generation_status, DailyPattern.GenerationStatus.FALLBACK)
        self.assertEqual(pattern.algorithm_version, 1)

    def test_no_fallback_raises_when_no_previous_pattern(self):
        with self.assertRaises(NoFallbackAvailable):
            generate_daily_pattern(ROTATION_EPOCH, 1, fake_failure)


class FallbackRetryTests(TestCase):
    def setUp(self):
        Region.objects.all().update(is_active=False)
        self.region_a = make_region("Регіон А", rotation_order=1)
        self.region_b = make_region("Регіон Б", rotation_order=2)
        self.day1 = ROTATION_EPOCH
        self.day2 = ROTATION_EPOCH + timedelta(days=1)
        generate_daily_pattern(self.day1, 1, fake_success)
        self.fallback = generate_daily_pattern(self.day2, 1, fake_failure)

    def test_fallback_uses_previous_day_region(self):
        self.assertEqual(self.fallback.region, self.region_a)

    def test_retry_restores_scheduled_region_and_content(self):
        user = get_user_model().objects.create_user(username="u", password="pass12345")
        SavedPattern.objects.create(user=user, pattern=self.fallback)

        pattern = retry_fallback_pattern(self.fallback, 2, fake_success)

        pattern.refresh_from_db()
        self.assertEqual(pattern.pk, self.fallback.pk)
        self.assertEqual(pattern.generation_status, DailyPattern.GenerationStatus.SUCCESS)
        self.assertEqual(pattern.region, self.region_b)
        self.assertEqual(pattern.svg_content, f"<svg>{self.day2}-{self.region_b.pk}</svg>")
        self.assertEqual(pattern.algorithm_version, 2)
        self.assertTrue(SavedPattern.objects.filter(pattern=pattern).exists())

    def test_failed_retry_keeps_fallback_untouched(self):
        with self.assertRaises(ValueError):
            retry_fallback_pattern(self.fallback, 2, fake_failure)
        self.fallback.refresh_from_db()
        self.assertEqual(self.fallback.generation_status, DailyPattern.GenerationStatus.FALLBACK)
        self.assertEqual(self.fallback.region, self.region_a)

    def test_retry_ignores_successful_patterns(self):
        success = DailyPattern.objects.get(date=self.day1)
        svg_before = success.svg_content
        retry_fallback_pattern(success, 2, fake_failure)
        success.refresh_from_db()
        self.assertEqual(success.svg_content, svg_before)

    @patch(
        "apps.patterns.management.commands.retry_fallback_patterns.build_svg_for_date", fake_success
    )
    def test_management_command_retries_all_fallbacks(self):
        from io import StringIO

        from django.core.management import call_command

        out = StringIO()
        call_command("retry_fallback_patterns", stdout=out)
        self.fallback.refresh_from_db()
        self.assertEqual(self.fallback.generation_status, DailyPattern.GenerationStatus.SUCCESS)
        self.assertIn("1", out.getvalue())

    @patch("apps.patterns.admin.build_svg_for_date", fake_success)
    def test_admin_action_retries_selected_fallbacks(self):
        admin_user = get_user_model().objects.create_superuser(
            username="boss", email="boss@example.com", password="pass12345"
        )
        self.client.force_login(admin_user)
        response = self.client.post(
            "/vd/patterns/dailypattern/",
            {"action": "retry_fallbacks", "_selected_action": [self.fallback.pk]},
        )
        self.assertEqual(response.status_code, 302)
        self.fallback.refresh_from_db()
        self.assertEqual(self.fallback.generation_status, DailyPattern.GenerationStatus.SUCCESS)


class RealGenerationDeterminismTests(TestCase):
    """Реальна генерація (build_svg_for_date): та сама дата - той самий SVG і порядок мотивів."""

    def setUp(self):
        self.region = make_region("Регіон А", rotation_order=1)
        self.diamond = Motif.objects.create(
            name="Ромб",
            meaning_description="Тест.",
            geometry_parameters={
                "base_points": [[2.5, 0], [0, 2.5], [2.5, 5]],
                "symmetry": "reflection_vertical",
                "params": {},
            },
            verification_status=Motif.VerificationStatus.VERIFIED,
        )
        self.wave = Motif.objects.create(
            name="Хвиля",
            meaning_description="Тест.",
            geometry_parameters={
                "base_points": [[0, 0], [5, 5], [10, 0]],
                "symmetry": "wallpaper_p1_horizontal",
                "params": {"step": 15, "repeats": 4},
            },
            verification_status=Motif.VerificationStatus.VERIFIED,
        )
        self.diamond.compatible_regions.add(self.region)
        self.wave.compatible_regions.add(self.region)

    def test_same_date_gives_identical_svg(self):
        svg1, motifs1 = build_svg_for_date(date(2026, 9, 1), self.region)
        svg2, motifs2 = build_svg_for_date(date(2026, 9, 1), self.region)
        self.assertEqual(svg1, svg2)
        self.assertEqual([m.pk for m in motifs1], [m.pk for m in motifs2])


class RaceConditionTests(TestCase):
    """
    Розділ 11.2 ТЗ: одночасні запити на одну дату мають створити рівно
    один запис. Симулюємо гонку: інший "паралельний запит" уже вставив
    запис у базу, поки наша перша перевірка (_get_existing_pattern)
    застаріло каже що запису ще нема — реалістичний race window без
    потреби піднімати реальні потоки в тесті.
    """

    def setUp(self):
        self.region = make_region("Регіон А", rotation_order=1)

    def test_concurrent_creation_returns_existing_not_error(self):
        pre_existing = DailyPattern.objects.create(
            date=ROTATION_EPOCH,
            region=self.region,
            seed="already-there",
            algorithm_version=1,
            svg_content="<svg>already-there</svg>",
            generation_status=DailyPattern.GenerationStatus.SUCCESS,
        )

        with patch("apps.patterns.services.generation._get_existing_pattern") as mock_get_existing:
            # Перший виклик - "застаріла" перевірка на початку generate_daily_pattern
            # (симулює момент ДО того, як паралельний запит устиг закомітити запис).
            # Другий виклик - повторне читання ПІСЛЯ пійманого IntegrityError,
            # де має повернутись уже реальний існуючий запис, не підмінений мок.
            mock_get_existing.side_effect = [None, pre_existing]
            result = generate_daily_pattern(ROTATION_EPOCH, 1, fake_success)

        self.assertEqual(result.pk, pre_existing.pk)
        self.assertEqual(DailyPattern.objects.filter(date=ROTATION_EPOCH).count(), 1)


class ErrorPagesTests(TestCase):
    """
    Розділ 5.14 ТЗ: 500-сторінка не залежить від бази даних/контексту
    запиту. Найточніший тест — відтворити РЕАЛЬНИЙ виклик Django
    (django.views.defaults.server_error робить template.render() БЕЗ
    аргументів: без request, без context processors) — а не імітувати
    "відключену БД" мокуванням, яке легко дало б хибний результат
    залежно від того, що саме замокано, і не довело б головного:
    чи шаблон взагалі не потребує контексту для рендеру.
    """

    def test_500_template_renders_without_request_or_db_context(self):
        html = render_to_string("500.html")
        self.assertIn("500", html)

    @override_settings(DEBUG=False)
    def test_unknown_url_returns_404_not_500(self):
        response = self.client.get("/this-page-does-not-exist/")
        self.assertEqual(response.status_code, 404)


class MissingCoverageTests(TestCase):
    """
    Пункт 22 плану Stage 2, буквально: "неіснуюча дата/регіон, коректний
    404" — три конкретні сценарії, виявлені зовнішньою рецензією,
    відсутні в попередній версії файлу.
    """

    def setUp(self):
        self.region = make_region("Регіон А", rotation_order=1)
        DailyPattern.objects.create(
            date=date(2026, 6, 1),
            region=self.region,
            seed="s1",
            algorithm_version=1,
            svg_content="<svg>1</svg>",
        )
        DailyPattern.objects.create(
            date=date(2026, 6, 10),
            region=self.region,
            seed="s2",
            algorithm_version=1,
            svg_content="<svg>2</svg>",
        )

    def test_pattern_detail_future_date_returns_404(self):
        future = date.today() + timedelta(days=5)
        response = self.client.get(f"/pattern/{future.isoformat()}/")
        self.assertEqual(response.status_code, 404)

    def test_region_detail_nonexistent_slug_returns_404(self):
        response = self.client.get("/regions/does-not-exist/")
        self.assertEqual(response.status_code, 404)


class SavedPatternToggleTests(TestCase):
    def setUp(self):
        self.region = make_region("Регіон А", rotation_order=1)
        self.pattern = DailyPattern.objects.create(
            date=date(2026, 6, 1),
            region=self.region,
            seed="s1",
            algorithm_version=1,
            svg_content="<svg>1</svg>",
        )
        self.user = get_user_model().objects.create_user(username="collector", password="pass12345")

    def test_anonymous_cannot_toggle_save(self):
        response = self.client.post(f"/pattern/{self.pattern.date}/save/")
        self.assertEqual(response.status_code, 302)
        self.assertIn("/accounts/login/", response.url)

    def test_authenticated_can_save_and_unsave(self):
        self.client.force_login(self.user)
        self.client.post(f"/pattern/{self.pattern.date}/save/")
        self.assertTrue(SavedPattern.objects.filter(user=self.user, pattern=self.pattern).exists())

        self.client.post(f"/pattern/{self.pattern.date}/save/")
        self.assertFalse(SavedPattern.objects.filter(user=self.user, pattern=self.pattern).exists())

    def test_toggle_redirects_to_internal_next(self):
        self.client.force_login(self.user)
        response = self.client.post(f"/pattern/{self.pattern.date}/save/", {"next": "/archive/"})
        self.assertEqual(response["Location"], "/archive/")

    def test_toggle_ignores_external_next(self):
        self.client.force_login(self.user)
        for next_url in ["https://evil.com/", "//evil.com", "/\\evil.com"]:
            response = self.client.post(f"/pattern/{self.pattern.date}/save/", {"next": next_url})
            self.assertEqual(response["Location"], f"/pattern/{self.pattern.date}/")

    def test_collection_shows_only_own_saved_patterns(self):
        other_user = get_user_model().objects.create_user(username="other", password="pass12345")
        SavedPattern.objects.create(user=other_user, pattern=self.pattern)

        self.client.force_login(self.user)
        response = self.client.get("/collection/")
        self.assertEqual(len(response.context["saved_patterns"]), 0)

    def test_anonymous_redirected_from_collection(self):
        response = self.client.get("/collection/")
        self.assertEqual(response.status_code, 302)
        self.assertIn("/accounts/login/", response.url)


class TourIndicatorTests(TestCase):
    def setUp(self):
        self.region = make_region("Регіон А", rotation_order=1)
        self.user = get_user_model().objects.create_user(username="tourist", password="pass12345")

    def test_same_day_save_counts_toward_tour(self):
        pattern = DailyPattern.objects.create(
            date=timezone.localdate(),
            region=self.region,
            seed="s1",
            algorithm_version=1,
            svg_content="<svg>1</svg>",
        )
        SavedPattern.objects.create(user=self.user, pattern=pattern)

        self.client.force_login(self.user)
        response = self.client.get("/collection/")
        self.assertEqual(response.context["tour_completed"], 1)

    def test_backdated_archive_save_does_not_count_toward_tour(self):
        old_pattern = DailyPattern.objects.create(
            date=date(2026, 1, 1),
            region=self.region,
            seed="s2",
            algorithm_version=1,
            svg_content="<svg>2</svg>",
        )
        SavedPattern.objects.create(user=self.user, pattern=old_pattern)

        self.client.force_login(self.user)
        response = self.client.get("/collection/")
        self.assertEqual(response.context["total_saved"], 1)
        self.assertEqual(response.context["tour_completed"], 0)

    def test_mixed_saves_count_only_valid_tour_entries(self):
        """Один користувач має і 'живе' збереження, і заднім числом —
        tour_completed рахує лише перше, не змішує й не подвоює."""
        other_region = make_region("Регіон Б", rotation_order=2)

        live_pattern = DailyPattern.objects.create(
            date=timezone.localdate(),
            region=self.region,
            seed="s3",
            algorithm_version=1,
            svg_content="<svg>3</svg>",
        )
        backdated_pattern = DailyPattern.objects.create(
            date=date(2026, 1, 1),
            region=other_region,
            seed="s4",
            algorithm_version=1,
            svg_content="<svg>4</svg>",
        )
        SavedPattern.objects.create(user=self.user, pattern=live_pattern)
        SavedPattern.objects.create(user=self.user, pattern=backdated_pattern)

        self.client.force_login(self.user)
        response = self.client.get("/collection/")
        self.assertEqual(response.context["total_saved"], 2)
        self.assertEqual(response.context["tour_completed"], 1)


class StreakTests(TestCase):
    def setUp(self):
        self.region = make_region("Регіон А", rotation_order=1)
        self.user = get_user_model().objects.create_user(username="streaker", password="pass12345")

    def test_first_save_sets_streak_to_one(self):
        pattern = DailyPattern.objects.create(
            date=timezone.localdate(),
            region=self.region,
            seed="s1",
            algorithm_version=1,
            svg_content="<svg>1</svg>",
        )
        self.client.force_login(self.user)
        self.client.post(f"/pattern/{pattern.date}/save/")
        self.user.profile.refresh_from_db()
        self.assertEqual(self.user.profile.current_streak, 1)

    def test_consecutive_day_increments_streak(self):
        self.user.profile.current_streak = 3
        self.user.profile.last_active_date = timezone.localdate() - timedelta(days=1)
        self.user.profile.save()

        today_pattern = DailyPattern.objects.create(
            date=timezone.localdate(),
            region=self.region,
            seed="s3",
            algorithm_version=1,
            svg_content="<svg>3</svg>",
        )
        self.client.force_login(self.user)
        self.client.post(f"/pattern/{today_pattern.date}/save/")
        self.user.profile.refresh_from_db()
        self.assertEqual(self.user.profile.current_streak, 4)

    def test_gap_day_resets_streak_to_one(self):
        pattern = DailyPattern.objects.create(
            date=timezone.localdate(),
            region=self.region,
            seed="s4",
            algorithm_version=1,
            svg_content="<svg>4</svg>",
        )
        self.user.profile.current_streak = 10
        self.user.profile.last_active_date = timezone.localdate() - timedelta(days=3)
        self.user.profile.save()

        self.client.force_login(self.user)
        self.client.post(f"/pattern/{pattern.date}/save/")
        self.user.profile.refresh_from_db()
        self.assertEqual(self.user.profile.current_streak, 1)


class BreadcrumbsTests(TestCase):
    def setUp(self):
        self.region = make_region("Регіон Б", rotation_order=50)

    def test_region_breadcrumbs_end_without_url(self):
        """Остання крихта - поточна сторінка, вона не має бути посиланням."""
        crumbs = self.region.breadcrumbs
        self.assertEqual(crumbs[-1]["label"], self.region.name)
        self.assertNotIn("url", crumbs[-1])

    def test_pattern_breadcrumbs_include_region_link(self):
        pattern = DailyPattern.objects.create(
            date=date(2026, 3, 3),
            region=self.region,
            seed="bc1",
            algorithm_version=1,
            svg_content="<svg></svg>",
        )
        labels = [c["label"] for c in pattern.breadcrumbs]
        self.assertIn(self.region.name, labels)

    def test_breadcrumbs_render_on_region_page(self):
        response = self.client.get(f"/regions/{self.region.slug}/")
        self.assertContains(response, "Головна")


class HomepageStatusBarTests(TestCase):
    def setUp(self):
        self.region = make_region("Регіон В", rotation_order=51)
        self.user = get_user_model().objects.create_user(username="visitor", password="pass12345")

    def test_anonymous_sees_signup_call_not_streak_numbers(self):
        response = self.client.get("/")
        self.assertContains(response, "Створити акаунт")
        self.assertContains(response, "Реєстрація не обов'язкова")
        self.assertNotContains(response, "днів поспіль")

    def test_authenticated_sees_streak_and_tour(self):
        self.client.force_login(self.user)
        response = self.client.get("/")
        self.assertContains(response, "днів поспіль")
        self.assertContains(response, "регіонів пройдено")

    def test_anonymous_page_does_not_crash_without_profile(self):
        """AnonymousUser не має profile - шаблон не повинен на цьому падати."""
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)


class LandingSectionTests(TestCase):
    def test_landing_toggle_present_on_homepage(self):
        response = self.client.get("/")
        self.assertContains(response, "Що таке VyshyvankaDaily")
        self.assertContains(response, 'aria-controls="landing-body"')


class RegionListViewTests(TestCase):
    def test_returns_200_and_lists_verified_regions(self):
        make_region("Видимий регіон", 1, verified=True)
        make_region("Непідтверджений регіон", 2, verified=False)
        response = self.client.get("/regions/")
        names = [r.name for r in response.context["regions"]]
        self.assertIn("Видимий регіон", names)
        self.assertNotIn("Непідтверджений регіон", names)


@override_settings(DEBUG=True)
class DebugViewsEnabledTests(TestCase):
    def setUp(self):
        self.region = make_region("Дебаг регіон", 1)

    def test_debug_pattern_view_returns_200(self):
        response = self.client.get(f"/patterns/debug/{timezone.localdate().isoformat()}/")
        self.assertEqual(response.status_code, 200)

    def test_debug_pattern_view_rejects_bad_date(self):
        response = self.client.get("/patterns/debug/not-a-date/")
        self.assertEqual(response.status_code, 404)

    def test_debug_all_regions_view_returns_200(self):
        response = self.client.get("/patterns/debug/all-regions/")
        self.assertEqual(response.status_code, 200)


class DebugViewsDisabledTests(TestCase):
    def test_debug_pattern_view_404_when_debug_off(self):
        response = self.client.get(f"/patterns/debug/{timezone.localdate().isoformat()}/")
        self.assertEqual(response.status_code, 404)

    def test_debug_all_regions_view_404_when_debug_off(self):
        response = self.client.get("/patterns/debug/regions/")
        self.assertEqual(response.status_code, 404)


class PatternDetailIsTodayTests(TestCase):
    def setUp(self):
        self.region = make_region("Сьогоднішній регіон", 1)

    def test_is_today_true_for_current_date(self):
        pattern = DailyPattern.objects.create(
            date=timezone.localdate(),
            region=self.region,
            seed="today",
            algorithm_version=1,
            svg_content="<svg>today</svg>",
        )
        response = self.client.get(f"/pattern/{pattern.date.isoformat()}/")
        self.assertTrue(response.context["is_today"])

    def test_is_today_false_for_past_date(self):
        past_date = timezone.localdate() - timedelta(days=3)
        pattern = DailyPattern.objects.create(
            date=past_date,
            region=self.region,
            seed="past",
            algorithm_version=1,
            svg_content="<svg>past</svg>",
        )
        response = self.client.get(f"/pattern/{pattern.date.isoformat()}/")
        self.assertFalse(response.context["is_today"])


class RegionAdminTests(TestCase):
    def test_verification_badge_verified(self):
        from django.contrib import admin as django_admin

        from apps.patterns.admin import RegionAdmin

        region = make_region("Адмін регіон", 1, verified=True)
        admin_instance = RegionAdmin(Region, django_admin.site)
        badge = admin_instance.verification_badge(region)
        self.assertIn("#3A7D2C", badge)

    def test_keyword_badge_dash_when_empty(self):
        from django.contrib import admin as django_admin

        from apps.patterns.admin import RegionAdmin

        region = make_region("Регіон без ключа", 2)
        admin_instance = RegionAdmin(Region, django_admin.site)
        badge = admin_instance.keyword_badge(region)
        self.assertIn(">-<", badge)

    def test_palette_preview_empty_returns_dash(self):
        from django.contrib import admin as django_admin

        from apps.patterns.admin import RegionAdmin

        region = make_region("Регіон без кольорів", 3)
        region.dominant_colors = []
        region.save()
        admin_instance = RegionAdmin(Region, django_admin.site)
        self.assertEqual(admin_instance.palette_preview(region), "-")

    def test_mark_verified_action(self):
        from django.contrib import admin as django_admin

        from apps.patterns.admin import RegionAdmin

        region = make_region("Регіон на перевірці", 4, verified=False)
        admin_instance = RegionAdmin(Region, django_admin.site)
        request = RequestFactory().get("/vd/")
        request.session = {}
        request._messages = FallbackStorage(request)
        admin_instance.mark_verified(request, Region.objects.filter(pk=region.pk))
        region.refresh_from_db()
        self.assertEqual(region.verification_status, Region.VerificationStatus.VERIFIED)


class PatternDetailUrlTests(TestCase):
    def setUp(self):
        region = make_region("Регіон А", rotation_order=1)
        DailyPattern.objects.create(
            date=date(2026, 6, 1),
            region=region,
            seed="s1",
            algorithm_version=1,
            svg_content="<svg>1</svg>",
        )

    def test_canonical_date_url_works(self):
        self.assertEqual(self.client.get("/pattern/2026-06-01/").status_code, 200)

    def test_non_canonical_date_formats_are_404(self):
        for value in ["20260601", "2026-W22-1", "2026-06-01T00:00"]:
            self.assertEqual(self.client.get(f"/pattern/{value}/").status_code, 404, value)

    def test_past_pattern_has_single_noindex_robots_tag(self):
        response = self.client.get("/pattern/2026-06-01/")
        robots = re.findall(r'<meta name="robots" content="([^"]+)"', response.content.decode())
        self.assertEqual(robots, ["noindex, follow"])


class HomepageUnavailableTests(TestCase):
    def test_no_active_regions_shows_friendly_page_instead_of_500(self):
        Region.objects.update(is_active=False)
        response = self.client.get("/")
        self.assertEqual(response.status_code, 503)
        self.assertContains(response, "Орнамент дня готується", status_code=503)

    @patch("apps.patterns.views.build_svg_for_date", side_effect=RuntimeError("boom"))
    def test_generation_failure_without_fallback_shows_friendly_page(self, _mock):
        make_region("Регіон А", rotation_order=1)
        response = self.client.get("/")
        self.assertEqual(response.status_code, 503)


class ListPaginationTests(TestCase):
    def setUp(self):
        self.region = make_region("Регіон П", rotation_order=90)
        self.user = get_user_model().objects.create_user(username="p", password="pass12345")
        for i in range(15):
            pattern = DailyPattern.objects.create(
                date=date(2026, 1, 1) + timedelta(days=i),
                region=self.region,
                seed=f"s{i}",
                algorithm_version=1,
                svg_content="<svg></svg>",
            )
            SavedPattern.objects.create(user=self.user, pattern=pattern)

    def test_region_page_has_no_pattern_grid(self):
        response = self.client.get(f"/regions/{self.region.slug}/")
        self.assertNotIn("patterns", response.context)
        self.assertNotContains(response, f"/archive/?region={self.region.slug}")
        self.assertNotContains(response, "?page=2")

    def test_collection_shows_12_per_page_and_full_total(self):
        self.client.force_login(self.user)
        response = self.client.get("/collection/")
        self.assertEqual(len(response.context["saved_patterns"]), 12)
        self.assertEqual(response.context["total_saved"], 15)
        self.assertEqual(len(self.client.get("/collection/?page=2").context["saved_patterns"]), 3)

    def test_collection_does_not_load_svg_content(self):
        # SVG картки йде окремим <img>, тож важкий текст із бази не тягнемо
        self.client.force_login(self.user)
        saved = self.client.get("/collection/").context["saved_patterns"][0]
        self.assertIn("svg_content", saved.pattern.get_deferred_fields())

    def test_invalid_page_falls_back_gracefully(self):
        response = self.client.get(f"/regions/{self.region.slug}/?page=abc")
        self.assertEqual(response.status_code, 200)


class QueryCountTests(TestCase):
    """Кількість запитів не росте з кількістю карток (захист від N+1)."""

    def setUp(self):
        self.user = get_user_model().objects.create_user(username="q", password="pass12345")
        self.regions = [make_region(f"Регіон Q{i}", rotation_order=200 + i) for i in range(10)]

    def _add_patterns(self, count, region=None):
        for i in range(count):
            pattern = DailyPattern.objects.create(
                date=date(2026, 3, 1) + timedelta(days=DailyPattern.objects.count()),
                region=region or self.regions[i % len(self.regions)],
                seed=f"q{i}",
                algorithm_version=1,
                svg_content="<svg></svg>",
            )
            SavedPattern.objects.create(user=self.user, pattern=pattern)

    def _queries(self, url):
        from django.db import connection
        from django.test.utils import CaptureQueriesContext

        with CaptureQueriesContext(connection) as ctx:
            self.assertEqual(self.client.get(url).status_code, 200)
        return len(ctx.captured_queries)

    def _assert_constant(self, url, region=None):
        self._add_patterns(1, region)
        few = self._queries(url)
        self._add_patterns(9, region)
        self.assertEqual(self._queries(url), few)

    def test_region_page(self):
        self._assert_constant(f"/regions/{self.regions[0].slug}/", region=self.regions[0])

    def test_collection(self):
        self.client.force_login(self.user)
        self._assert_constant("/collection/")


class DominantColorsValidationTests(TestCase):
    def setUp(self):
        self.region = make_region("Регіон Колір", rotation_order=300)

    def _region(self, colors):
        self.region.dominant_colors = colors
        return self.region

    def test_valid_hex_colors_pass(self):
        self._region(["#FF6B35", "#004e89"]).full_clean()

    def test_invalid_values_rejected(self):
        from django.core.exceptions import ValidationError

        for bad in [["red"], ["#FFF"], ['#000000" onload="x'], "#000000", [], [123]]:
            with self.assertRaises(ValidationError, msg=repr(bad)):
                self._region(bad).full_clean()


class RegionEnglishContentTests(TestCase):
    def setUp(self):
        self.region = make_region("Регіон Мова", rotation_order=400)

    def test_english_page_falls_back_to_ukrainian_until_translated(self):
        response = self.client.get(f"/en/regions/{self.region.slug}/")
        self.assertContains(response, "Тестовий опис.")

    def test_english_page_shows_english_text_when_present(self):
        self.region.symbolism_description_en = "<p>English symbolism.</p>"
        self.region.save()
        self.assertContains(
            self.client.get(f"/en/regions/{self.region.slug}/"), "English symbolism."
        )
        uk = self.client.get(f"/regions/{self.region.slug}/")
        self.assertContains(uk, "Тестовий опис.")
        self.assertNotContains(uk, "English symbolism.")

    def test_both_languages_are_sanitized(self):
        self.region.symbolism_description_uk = "<p>Укр</p><script>alert(1)</script>"
        self.region.symbolism_description_en = "<p>Eng</p><script>alert(2)</script>"
        self.region.save()
        self.region.refresh_from_db()
        self.assertNotIn("<script>", self.region.symbolism_description_uk)
        self.assertNotIn("<script>", self.region.symbolism_description_en)


class LoadRegionContentTests(TestCase):
    def setUp(self):
        import json
        import tempfile

        self.region = make_region("Регіон Файл", rotation_order=500)
        entry = {
            "slug": self.region.slug,
            "target_keyword": "ключ",
            "seo_title": "Заголовок",
            "seo_description": "Опис",
            "symbolism_description_html": "<p>Новий текст</p>",
            "en": {
                "target_keyword": "keyword",
                "seo_title": "Title",
                "seo_description": "Description",
                "symbolism_description_html": "<p>New text</p>",
            },
        }
        self.path = tempfile.mktemp(suffix=".json")
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump([entry], f, ensure_ascii=False)

    def _run(self, *args):
        from io import StringIO

        from django.core.management import call_command

        out = StringIO()
        call_command("load_region_content", self.path, *args, stdout=out)
        self.region.refresh_from_db()
        return out.getvalue()

    def test_loads_both_languages(self):
        self._run()
        self.assertEqual(self.region.symbolism_description_uk, "<p>Новий текст</p>")
        self.assertEqual(self.region.symbolism_description_en, "<p>New text</p>")
        self.assertEqual(self.region.seo_title_en, "Title")
        self.assertEqual(self.region.target_keyword_uk, "ключ")

    def test_dry_run_changes_nothing(self):
        self._run("--dry-run")
        self.assertEqual(self.region.symbolism_description_uk, "Тестовий опис.")
        self.assertIsNone(self.region.symbolism_description_en)

    def test_check_reports_differences_without_writing(self):
        out = self._run("--check")
        self.assertIn(self.region.slug, out)
        import hashlib

        digest = hashlib.sha256("Тестовий опис.".encode()).hexdigest()[:12]
        self.assertIn(f"(база {digest})", out)
        self.assertEqual(self.region.symbolism_description_uk, "Тестовий опис.")
        self._run()
        self.assertIn("збігаються", self._run("--check"))


class ExportRegionContentTests(TestCase):
    def test_export_is_ascii_and_round_trips_through_loader(self):
        import json
        import tempfile
        from io import StringIO

        from django.core.management import call_command

        region = make_region("Регіон Експорт", rotation_order=600)
        region.seo_title_uk = "Заголовок «з лапками»"
        region.symbolism_description_en = "<p>English</p>"
        region.save()

        out = StringIO()
        call_command("export_region_content", region.slug, stdout=out)
        raw = out.getvalue()
        self.assertTrue(raw.isascii())
        data = json.loads(raw)
        self.assertEqual(data[0]["seo_title"], "Заголовок «з лапками»")
        self.assertEqual(data[0]["en"]["symbolism_description_html"], "<p>English</p>")

        path = tempfile.mktemp(suffix=".json")
        with open(path, "w", encoding="utf-8") as f:
            f.write(raw)
        check = StringIO()
        call_command("load_region_content", path, "--check", stdout=check)
        self.assertIn("збігаються", check.getvalue())


class ViewCountColumnDroppedTests(TestCase):
    def test_no_view_count_column(self):
        from django.db import connection

        from apps.blog.models import BlogPost

        for model in (DailyPattern, BlogPost):
            with connection.cursor() as cursor:
                columns = [
                    c.name
                    for c in connection.introspection.get_table_description(
                        cursor, model._meta.db_table
                    )
                ]
            self.assertNotIn("view_count", columns)


class PatternSvgEndpointTests(TestCase):
    def setUp(self):
        self.region = make_region("SVG регіон", 1)
        self.pattern = DailyPattern.objects.create(
            date=date(2026, 9, 1),
            region=self.region,
            seed="s",
            algorithm_version=1,
            svg_content='<svg xmlns="http://www.w3.org/2000/svg"><rect/></svg>',
        )

    def test_serves_cached_svg(self):
        response = self.client.get("/pattern/2026-09-01.svg")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "image/svg+xml; charset=utf-8")
        self.assertIn("immutable", response["Cache-Control"])
        self.assertContains(response, "<rect/>")

    def test_missing_or_noncanonical_date_is_404(self):
        self.assertEqual(self.client.get("/pattern/2026-09-02.svg").status_code, 404)
        self.assertEqual(self.client.get("/pattern/20260901.svg").status_code, 404)

    def test_thumbnail_include_uses_img_with_alt(self):
        from django.utils import translation

        with translation.override("uk"):
            html = render_to_string("includes/pattern_img.html", {"pattern": self.pattern})
        self.assertIn('src="/pattern/2026-09-01.svg?v=', html)
        self.assertRegex(html, r'alt="Орнамент: SVG регіон, 01 \w+ 2026"')
        self.assertNotIn("<rect/>", html)

    def test_pattern_page_hero_label_follows_language(self):
        html = self.client.get("/en/pattern/2026-09-01/").content.decode()
        self.assertIn('class="vd-hero__art" role="img" aria-label="Pattern: ', html)


class SourceReferenceTextOnlyTests(TestCase):
    def test_urls_and_labels_removed_bibliography_kept(self):
        from apps.patterns.templatetags.source_tags import source_reference

        cases = {
            "К.: 1988. Повний текст: archive.org/stream/x": "К.: 1988.",
            "chtyvo.org.ua/authors/Schybria_Volodymyr/. 2017.": "2017.",
            "К.: Мистецтво, 2008. Національна премія ім. Т.Шевченка, 2012.": (
                "К.: Мистецтво, 2008. Національна премія ім. Т.Шевченка, 2012."
            ),
            "Режим доступу: https://honchar.org.ua/to-learn/x-i198": "",
            "ich.unesco.org, внесено 16.12.2021.": "внесено 16.12.2021.",
        }
        for ref, expected in cases.items():
            self.assertEqual(source_reference(ref), expected, ref)

    def test_rendered_without_links_and_escaped(self):
        from django.template import Context, Template

        out = Template("{% load source_tags %}{{ r|source_reference }}").render(
            Context({"r": "Повний текст: archive.org/x <script>"})
        )
        self.assertNotIn("<a ", out)
        self.assertNotIn("archive.org", out)
        self.assertIn("&lt;script&gt;", out)


class AccentColorsTests(TestCase):
    def test_accent_row_shown_only_when_set(self):
        region = make_region("Кольоровий регіон", 1)
        url = f"/regions/{region.slug}/"
        self.assertNotContains(self.client.get(url), "Також трапляються")
        region.accent_colors = ["#2E7D32"]
        region.save()
        response = self.client.get(url)
        self.assertContains(response, "Також трапляються")
        self.assertContains(response, 'style="background-color: #2E7D32;"')

    def test_accent_colors_validated(self):
        region = make_region("Регіон", 1)
        from django.core.exceptions import ValidationError

        region.accent_colors = ["red"]
        with self.assertRaises(ValidationError):
            region.full_clean()

    def test_seeded_regions_keep_generator_palette(self):
        region = Region.objects.filter(slug="poltavska-oblast").first()
        if region is None:
            self.skipTest("немає seed-регіонів")
        self.assertEqual(region.accent_colors, ["#D00000", "#6EC6E8", "#C8913A"])
        self.assertNotIn("#D00000", region.dominant_colors)


class GeneratorOnlyColorsTests(TestCase):
    def test_hidden_colors_not_shown_but_kept_for_generator(self):
        region = make_region("Прихований колір", 1)
        region.dominant_colors = ["#FFFFFF", "#5B2C83", "#D00000"]
        region.generator_only_colors = ["#5B2C83"]
        region.save()
        self.assertEqual(region.shown_colors, ["#FFFFFF", "#D00000"])
        html = self.client.get(f"/regions/{region.slug}/").content.decode()
        self.assertNotIn("background-color: #5B2C83", html)
        self.assertIn("background-color: #D00000", html)
        listing = self.client.get("/regions/").content.decode()
        card = re.search(rf'href="/regions/{region.slug}/" class="vd-card">.*?</a>', listing, re.S)
        self.assertNotIn("#5B2C83", card.group(0))
        self.assertIn("background-color: #D00000", card.group(0))

    def test_seeded_kyiv_hides_unconfirmed_colors(self):
        region = Region.objects.filter(slug="kyivska-oblast").first()
        if region is None:
            self.skipTest("немає seed-регіонів")
        self.assertNotIn("#5B2C83", region.shown_colors)
        self.assertIn("#5B2C83", region.dominant_colors)


class HomepageStructureTests(TestCase):
    def setUp(self):
        self.region = make_region("Регіон Г", rotation_order=52)

    def test_single_keyword_h1_and_region_of_day_in_h2(self):
        import re

        html = self.client.get("/").content.decode()
        h1 = re.findall(r"<h1[^>]*>(.*?)</h1>", html, re.S)
        self.assertEqual(len(h1), 1)
        self.assertIn("Орнамент вишиванки різних регіонів України", h1[0])
        region_h2 = re.findall(r'<h2 class="vd-hero__region">(.*?)</h2>', html, re.S)
        self.assertEqual(len(region_h2), 1)
        self.assertTrue(region_h2[0].strip())

    def test_english_home_has_english_h1(self):
        html = self.client.get("/en/").content.decode()
        self.assertIn(
            '<h1 class="vd-intro__title">Ukrainian Embroidery Patterns from Every Region</h1>', html
        )

    def test_region_groups_link_every_region(self):
        html = self.client.get("/").content.decode()
        self.assertIn('role="tablist"', html)
        self.assertIn(f'href="/regions/{self.region.slug}/"', html)

    def test_footer_labels_are_not_headings(self):
        html = self.client.get("/").content.decode()
        footer = html[html.index("<footer") :]
        self.assertNotIn("<h2", footer)


class LanguageSwitcherLinkTests(TestCase):
    def test_switcher_is_plain_links_crawlers_can_follow(self):
        region = make_region("Мовний регіон", 53)
        html = self.client.get(f"/regions/{region.slug}/").content.decode()
        self.assertIn(f'href="/en/regions/{region.slug}/" hreflang="en"', html)
        self.assertNotIn('action="/i18n/setlang/"', html)
        html_en = self.client.get(f"/en/regions/{region.slug}/").content.decode()
        self.assertIn(f'href="/regions/{region.slug}/" hreflang="uk"', html_en)


class RegionGroupsTests(TestCase):
    def test_short_name_follows_language(self):
        from django.utils import translation

        region = Region(slug="poltavska-oblast", name="Полтавська область")
        with translation.override("uk"):
            self.assertEqual(region.short_name, "Полтавщина")
        with translation.override("en"):
            self.assertEqual(region.short_name, "Poltava")

    def test_unknown_slug_kept_in_groups(self):
        from apps.patterns.region_groups import grouped_regions

        known = Region(slug="lvivska-oblast", name="Львівська область")
        extra = Region(slug="new-region", name="Новий регіон")
        groups = grouped_regions([known, extra])
        slugs = [r.slug for g in groups for r in g["regions"]]
        self.assertEqual(sorted(slugs), ["lvivska-oblast", "new-region"])

    def test_region_list_has_group_h2(self):
        make_region("Регіон Д", 54)
        html = self.client.get("/regions/").content.decode()
        self.assertIn('<h2 class="vd-section-title">', html)


class StripeColorsTests(TestCase):
    def test_stripe_merges_shown_and_accent_without_hidden_or_duplicates(self):
        region = Region(
            slug="x",
            name="X",
            dominant_colors=["#FFFFFF", "#5B2C83", "#D00000"],
            generator_only_colors=["#5B2C83"],
            accent_colors=["#D00000", "#C8913A"],
        )
        self.assertEqual(region.stripe_colors, ["#FFFFFF", "#D00000", "#C8913A"])


class RegionMapTests(TestCase):
    def setUp(self):
        from django.core.cache import cache

        cache.clear()

    def test_regions_page_keeps_list_and_adds_map_links(self):
        html = self.client.get("/regions/").content.decode()
        verified = Region.objects.verified().count()
        self.assertIn("data-vd-map", html)
        self.assertEqual(html.count('class="vd-map__rg'), verified)
        self.assertGreaterEqual(html.count('class="vd-card"'), verified)
        self.assertIn('href="/regions/poltavska-oblast/"', html)

    def test_hover_zone_does_not_move_and_cities_have_bigger_target(self):
        html = self.client.get("/regions/").content.decode()
        verified = Region.objects.verified().count()
        self.assertEqual(html.count('class="vd-map__lift"'), verified)
        self.assertEqual(html.count('class="vd-map__hit"'), verified)
        cities = Region.objects.verified().filter(slug__in=["m-kyiv", "m-sevastopol"]).count()
        self.assertEqual(len(re.findall(r'<circle class="vd-map__hit"[^>]+r="13"', html)), cities)
        regions = re.findall(r'data-slug="([^"]+)"', html)
        self.assertEqual(
            regions[len(regions) - cities :], [s for s in regions if s.startswith("m-")]
        )
        cities_layer = html.split('vd-map__regions--cities">')[1].split("</g>\n")[0]
        self.assertEqual(cities_layer.count('class="vd-map__rg'), cities)

    def test_svg_numbers_are_not_localized(self):
        html = self.client.get("/regions/").content.decode()
        self.assertIsNone(re.search(r'c[xy]="\d+,\d', html))
        self.assertIsNone(re.search(r"translate\(\d+,\d", html))

    def test_english_map(self):
        html = self.client.get("/en/regions/").content.decode()
        self.assertIn("All of Ukraine", html)
        self.assertIn('href="/en/regions/poltavska-oblast/"', html)

    def test_pick_motif_prefers_most_stitches(self):
        from apps.patterns.services.region_map import motif_pattern, pick_motif

        region = make_region("Регіон М", 77)
        small = Motif.objects.create(
            name="Малий",
            geometry_parameters={"format": "pixel_grid_v1", "grid": ["#."], "palette": {"#": 0}},
        )
        big = Motif.objects.create(
            name="Великий",
            geometry_parameters={
                "format": "pixel_grid_v1",
                "grid": ["##", "#o"],
                "palette": {"#": 0, "o": 1},
            },
        )
        region.compatible_motifs.add(small, big)
        self.assertEqual(pick_motif(region), big)
        pattern = motif_pattern("x", ["#000000", "#FFFFFF"])
        self.assertIn('stroke="#000000"', pattern)
        self.assertIn('stroke="#FFFDF8"', pattern)

    def test_map_pattern_uses_generator_motif(self):
        from apps.patterns.services.gen2.catalog import flap_motif, palette
        from apps.patterns.services.region_map import motif_pattern

        pattern = motif_pattern("chernivetska-oblast", ["#000000"])
        self.assertIn('id="vd-m-chernivetska-oblast"', pattern)
        self.assertIn(f'stroke="{palette("chernivetska-oblast")[0]}"', pattern)
        self.assertGreater(flap_motif("chernivetska-oblast").w, 10)


class RegionPhotosTests(TestCase):
    def _write(self, entries):
        import json
        import tempfile

        f = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8")
        json.dump(entries, f, ensure_ascii=False)
        f.close()
        return f.name

    def test_load_region_photos_syncs_and_page_shows_gallery(self):
        from django.core.management import call_command

        from apps.patterns.models import RegionPhoto

        region = make_region("Регіон Ф", 88)
        entry = {
            "region": region.slug,
            "image": "/static/regions/x/a.webp",
            "thumbnail": "/static/regions/x/a-thumb.webp",
            "caption_uk": "Ілюстрація VyshyvankaDaily: тест.",
            "caption_en": "Illustration by VyshyvankaDaily: test.",
        }
        path = self._write([entry])
        call_command("load_region_photos", path, "--dry-run", stdout=StringIO())
        self.assertEqual(RegionPhoto.objects.count(), 0)
        call_command("load_region_photos", path, stdout=StringIO())
        call_command("load_region_photos", path, stdout=StringIO())
        self.assertEqual(RegionPhoto.objects.count(), 1)
        RegionPhoto.objects.create(
            region=region,
            image_url="https://example.org/real.jpg",
            thumbnail_url="https://example.org/t.jpg",
        )

        html = self.client.get(f"/regions/{region.slug}/").content.decode().split("<body", 1)[1]
        self.assertIn('id="gallery"', html)
        self.assertIn('class="vd-photo-strip__badge"', html)
        self.assertEqual(html.count("vd-photo-strip__badge"), 1)

        call_command("load_region_photos", self._write([]), stdout=StringIO())
        self.assertEqual(
            list(RegionPhoto.objects.values_list("image_url", flat=True)),
            ["https://example.org/real.jpg"],
        )

    def test_repo_photos_file_points_to_existing_files(self):
        import json
        from pathlib import Path

        from django.conf import settings

        root = Path(settings.BASE_DIR)
        entries = json.loads((root / "region_photos.json").read_text(encoding="utf-8"))
        self.assertGreaterEqual(len(entries), 27)
        for e in entries:
            for key in ("image", "thumbnail"):
                self.assertTrue((root / e[key].lstrip("/")).exists(), e[key])
            self.assertTrue(e["caption_uk"].startswith("Ілюстрація"))
            self.assertTrue(e["caption_en"].startswith("Illustration"))


class PatternRetentionTests(TestCase):
    def setUp(self):
        self.region = make_region("Регіон К", 300)
        self.user = get_user_model().objects.create_user(username="keep", password="pass12345")

    def _pattern(self, d):
        return DailyPattern.objects.create(
            date=d, region=self.region, seed=str(d), algorithm_version=1, svg_content="<svg/>"
        )

    def test_prune_keeps_last_27_days_and_saved(self):
        from apps.patterns.services.generation import KEEP_DAYS, prune_old_patterns

        today = date(2026, 10, 12)
        old = self._pattern(today - timedelta(days=KEEP_DAYS + 1))
        saved = self._pattern(today - timedelta(days=KEEP_DAYS + 2))
        recent = self._pattern(today - timedelta(days=KEEP_DAYS))
        SavedPattern.objects.create(user=self.user, pattern=saved)
        prune_old_patterns(today)
        dates = set(DailyPattern.objects.values_list("date", flat=True))
        self.assertNotIn(old.date, dates)
        self.assertIn(saved.date, dates)
        self.assertIn(recent.date, dates)

    def test_old_pattern_page_redirects_to_region_and_archive_redirects(self):
        response = self.client.get("/pattern/2026-01-05/")
        self.assertEqual(response.status_code, 302)
        self.assertIn("/regions/", response["Location"])
        response = self.client.get("/archive/")
        self.assertEqual(response.status_code, 301)
        self.assertEqual(response["Location"], "/regions/")


class SymbolsPageTests(TestCase):
    def test_symbols_page_ua_and_en(self):
        html = self.client.get("/symbols/").content.decode()
        self.assertIn("<h1>Символи на вишиванці", html)
        self.assertIn('"@type": "DefinedTermSet"', html)
        self.assertIn('href="/regions/vinnytska-oblast/"', html)
        self.assertIn('class="vd-sym__art"', html)
        self.assertNotIn("—", html)
        en = self.client.get("/en/symbols/").content.decode()
        self.assertIn("<h1>Ukrainian embroidery symbols", en)
        self.assertIn('"@id": "http://testserver/symbols/#symbol-romb"', html)
        self.assertIn('id="symbol-romb"', html)
        self.assertIn('"dateModified": "2026-10-12"', html)
        self.assertIn('<time datetime="2026-10-12">', html)
        self.assertIn('href="/en/regions/vinnytska-oblast/"', en)

    def test_symbols_in_nav_sitemap_and_llms(self):
        self.assertContains(self.client.get("/"), 'href="/symbols/"')
        self.assertContains(self.client.get("/sitemap.xml"), "/symbols/")
        self.assertContains(self.client.get("/llms.txt"), "/symbols/")
        self.assertContains(self.client.get("/llms-full.txt"), "Символи на вишиванці")

    def test_every_symbol_key_has_art(self):
        from apps.patterns.services.symbols import data

        keys = {s["key"] for g in data()["uk"]["groups"] for s in g["symbols"]}
        en_keys = {s["key"] for g in data()["en"]["groups"] for s in g["symbols"]}
        self.assertEqual(keys, en_keys)
        self.assertTrue(keys <= set(data()["art"]))
