import random
import re
import xml.etree.ElementTree as ET
from datetime import date, timedelta
from io import StringIO

from django.core.management import call_command
from django.test import SimpleTestCase, TestCase
from django.utils import translation

from apps.patterns.models import DailyPattern, Motif, Region
from apps.patterns.services.gen2 import REGIONS, render_region
from apps.patterns.services.gen2.regions import build_shirt
from apps.patterns.services.generation import CURRENT_ALGORITHM_VERSION
from apps.patterns.services.pattern_builder import build_svg_for_date

SVG_NS = "{http://www.w3.org/2000/svg}"


def _render(slug, seed=1):
    return render_region(slug, random.Random(seed), f"Орнамент {slug}")


class Gen2RenderTests(SimpleTestCase):
    """Генератор 2.0: усі 27 регіонів, валідний і компактний SVG."""

    def test_all_regions_present(self):
        self.assertEqual(len(REGIONS), 27)

    def test_every_region_renders_valid_svg(self):
        for slug in REGIONS:
            with self.subTest(slug=slug):
                svg = _render(slug)
                root = ET.fromstring(svg)
                self.assertEqual(root.tag, f"{SVG_NS}svg")
                self.assertEqual(root.get("role"), "img")
                self.assertEqual(root.get("aria-label"), f"Орнамент {slug}")

    def test_ids_unique_and_references_resolve(self):
        for slug in REGIONS:
            with self.subTest(slug=slug):
                svg = _render(slug)
                ids = re.findall(r'\sid="([^"]+)"', svg)
                self.assertEqual(len(ids), len(set(ids)))
                refs = set(re.findall(r"url\(#([^)]+)\)", svg)) | set(
                    re.findall(r'href="#([^"]+)"', svg)
                )
                self.assertFalse(refs - set(ids))

    def test_same_rng_gives_identical_svg(self):
        for slug in ("chernivetska-oblast", "poltavska-oblast", "ivano-frankivska-oblast"):
            self.assertEqual(_render(slug, 7), _render(slug, 7))

    def test_dates_give_variants(self):
        # варіанти мотивів і шнурків: за місяць не одна й та сама сорочка
        for slug in REGIONS:
            with self.subTest(slug=slug):
                variants = {_render(slug, seed) for seed in range(12)}
                self.assertGreater(len(variants), 1)

    def test_size_budget(self):
        # SVG вбудовується в HTML: тримаємо його компактним
        for slug in REGIONS:
            with self.subTest(slug=slug):
                self.assertLess(len(_render(slug)), 400_000)

    def test_collar_flaps_embroidered(self):
        for slug in REGIONS:
            with self.subTest(slug=slug):
                shirt = build_shirt(slug, random.Random(1))
                flap = shirt.layers["flap"]
                self.assertTrue(flap.crosses and flap.free)

    def test_ids_differ_between_dates(self):
        # кілька сорочок на одній сторінці не мають ділити id
        a, b = _render("volynska-oblast", 1), _render("volynska-oblast", 2)
        ids = [set(re.findall(r'\sid="([^"]+)"', svg)) for svg in (a, b)]
        self.assertFalse(ids[0] & ids[1])

    def test_regions_differ_from_each_other(self):
        svgs = {_render(slug) for slug in REGIONS}
        self.assertEqual(len(svgs), 27)

    def test_unknown_slug_uses_generic_recipe_with_region_colors(self):
        svg = render_region("nova-oblast", random.Random(1), "Орнамент", ["#FFFFFF", "#123456"])
        ET.fromstring(svg)
        self.assertIn("#123456", svg)


def _region(slug="chernivetska-oblast"):
    # регіони вже є в тестовій базі (міграції з даними)
    region = Region.objects.filter(slug=slug).first()
    if region is None:
        with translation.override("uk"):
            region = Region.objects.create(
                name="Чернівецька область",
                slug=slug,
                symbolism_description="Тестовий опис.",
                dominant_colors=["#000000"],
                shirt_cut_type="Тестовий крій",
                rotation_order=1,
                verification_status=Region.VerificationStatus.VERIFIED,
            )
    region.compatible_motifs.clear()
    motif = Motif.objects.create(
        name="Букет троянд",
        meaning_description="Тест.",
        geometry_parameters={"format": "pixel_grid_v1", "grid": ["#"], "palette": {"#": 0}},
        verification_status=Motif.VerificationStatus.VERIFIED,
    )
    motif.compatible_regions.add(region)
    return region, motif


class Gen2BuilderTests(TestCase):
    def test_build_svg_for_date_uses_region_recipe(self):
        region, motif = _region()
        svg, motifs = build_svg_for_date(date(2026, 11, 1), region)
        self.assertRegex(svg, r'id="vcv[0-9a-f]+b"')
        self.assertEqual(motifs, [motif])

    def test_build_svg_for_date_is_deterministic(self):
        region, _ = _region()
        day = date(2026, 11, 1)
        self.assertEqual(build_svg_for_date(day, region)[0], build_svg_for_date(day, region)[0])


class RegeneratePatternsCommandTests(TestCase):
    def setUp(self):
        self.region, self.motif = _region()
        self.old = DailyPattern.objects.create(
            date=date(2026, 10, 1),
            region=self.region,
            seed="2026-10-01",
            algorithm_version=CURRENT_ALGORITHM_VERSION - 1,
            svg_content="<svg>old</svg>",
            generation_status=DailyPattern.GenerationStatus.SUCCESS,
        )
        self.fresh = DailyPattern.objects.create(
            date=date(2026, 10, 1) + timedelta(days=1),
            region=self.region,
            seed="2026-10-02",
            algorithm_version=CURRENT_ALGORITHM_VERSION,
            svg_content="<svg>fresh</svg>",
            generation_status=DailyPattern.GenerationStatus.SUCCESS,
        )

    def test_dry_run_changes_nothing(self):
        out = StringIO()
        call_command("regenerate_patterns", "--dry-run", stdout=out)
        self.assertIn("1", out.getvalue())
        self.old.refresh_from_db()
        self.assertEqual(self.old.svg_content, "<svg>old</svg>")

    def test_regenerates_only_stale_patterns_in_place(self):
        call_command("regenerate_patterns", stdout=StringIO())
        self.old.refresh_from_db()
        self.fresh.refresh_from_db()
        self.assertEqual(self.old.algorithm_version, CURRENT_ALGORITHM_VERSION)
        self.assertTrue(self.old.svg_content.startswith("<svg viewBox"))
        self.assertEqual(self.old.date, date(2026, 10, 1))
        self.assertEqual(list(self.old.motifs_used.all()), [self.motif])
        self.assertEqual(self.fresh.svg_content, "<svg>fresh</svg>")


class RegionMotifTilesTests(TestCase):
    def test_every_region_has_valid_tiles(self):
        from apps.patterns.services.gen2.catalog import region_tiles

        for slug in REGIONS:
            with self.subTest(slug=slug):
                groups = region_tiles(slug, "uk")
                self.assertTrue(groups)
                svgs = [svg for _, tiles in groups for svg, _, _ in tiles]
                ids = []
                for svg in svgs:
                    ET.fromstring(svg)
                    ids += re.findall(r'\sid="([^"]+)"', svg)
                self.assertEqual(len(ids), len(set(ids)))

    def test_symbol_anchors_exist_on_symbols_page(self):
        from apps.patterns.services.gen2.catalog import NAMES

        html = self.client.get("/symbols/").content.decode()
        for anchor in {a for _, _, a in NAMES.values() if a}:
            with self.subTest(anchor=anchor):
                self.assertIn(f'id="{anchor}"', html)

    def test_region_page_shows_motifs_ua_and_en(self):
        html = self.client.get("/regions/chernivetska-oblast/").content.decode()
        self.assertIn('id="motifs"', html)
        self.assertIn('href="#motifs"', html)
        self.assertIn('class="vd-motif__art"', html)
        self.assertIn('href="/symbols/#symbol-', html)
        en = self.client.get("/en/regions/chernivetska-oblast/").content.decode()
        self.assertIn('href="/en/symbols/#symbol-', en)
        ids = re.findall(r'\sid="([^"]+)"', html)
        self.assertEqual(len(ids), len(set(ids)))


class SymbolsPageArtTests(TestCase):
    def test_symbol_art_ids_unique_on_page(self):
        html = self.client.get("/symbols/").content.decode()
        self.assertIn('class="vd-sym__art"', html)
        ids = re.findall(r'\sid="([^"]+)"', html)
        self.assertEqual(len(ids), len(set(ids)))
