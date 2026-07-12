from django.test import TestCase

from apps.patterns.models import Region


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
