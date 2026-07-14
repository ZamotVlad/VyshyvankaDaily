from datetime import date, timedelta
from unittest.mock import patch

from django.template.loader import render_to_string
from django.test import TestCase, override_settings

from apps.patterns.models import DailyPattern, Motif, Region
from apps.patterns.services.generation import NoFallbackAvailable, generate_daily_pattern
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


class RealGenerationDeterminismTests(TestCase):
    """
    Gap 2 з рецензії: попередні тести генерації використовували підставну
    функцію, не реальну геометрію. Цей тест викликає build_svg_for_date
    напряму — справжня apply_symmetry + render_pattern_svg разом.

    Це також непрямий, але реальний regression-тест на Gap 1 (порядок
    мотивів): render_pattern_svg кодує порядок у самому SVG — індекс
    мотиву визначає його зону й колір (zone_names[i % len]). Якби
    .order_by("pk") зник чи порядок став нестабільним, svg1 != svg2
    міг би статись навіть із тим самим seed. Попередній варіант цього
    файлу містив окремий тест test_motif_order_is_explicit_not_incidental,
    який ніби мав перевіряти саме це, але по суті нічого не звіряв між
    двома викликами (хибне покриття) — видалений за рецензією.
    """

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


class ArchiveViewTests(TestCase):
    def setUp(self):
        self.region = make_region("Регіон А", rotation_order=1)
        DailyPattern.objects.create(
            date=date(2026, 6, 1),
            region=self.region,
            seed="s1",
            algorithm_version=1,
            svg_content="<svg>1</svg>",
        )

    def test_archive_returns_200(self):
        response = self.client.get("/archive/")
        self.assertEqual(response.status_code, 200)

    def test_filter_by_nonexistent_region_gives_empty_state(self):
        response = self.client.get("/archive/?region=does-not-exist")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["invalid_region_filter"])
        self.assertEqual(len(response.context["page_obj"].object_list), 0)

    def test_filter_by_deactivated_region_gives_empty_state(self):
        self.region.is_active = False
        self.region.save()
        response = self.client.get(f"/archive/?region={self.region.slug}")
        self.assertTrue(response.context["invalid_region_filter"])


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

    def test_archive_date_range_filter(self):
        response = self.client.get("/archive/?date_from=2026-06-05&date_to=2026-06-15")
        self.assertEqual(response.status_code, 200)
        dates_in_result = [p.date for p in response.context["page_obj"]]
        self.assertEqual(dates_in_result, [date(2026, 6, 10)])
