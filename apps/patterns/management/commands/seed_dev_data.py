from django.core.management.base import BaseCommand

from apps.patterns.models import Motif, Region, Source


class Command(BaseCommand):
    help = (
        "Наповнює dev-базу мінімальним набором тестових регіонів/мотивів "
        "для локальної розробки. НЕ фінальний достовірний контент "
        "(Roadmap Stage 2)."
    )

    def handle(self, *args, **options):
        source, _ = Source.objects.get_or_create(
            name="Тестове джерело (dev-seed)",
            defaults={
                "source_type": Source.SourceType.OTHER,
                "author_or_institution": "Dev seed",
                "reference": "https://example.com",
            },
        )

        region, _ = Region.objects.get_or_create(
            name="Тестовий регіон",
            defaults={
                "symbolism_description": "Тимчасовий опис для локальної розробки.",
                "dominant_colors": ["#D85A30", "#0F6E56"],
                "shirt_cut_type": "Тестовий крій",
                "rotation_order": 1,
                "verification_status": Region.VerificationStatus.VERIFIED,
            },
        )
        region.sources.add(source)

        diamond, _ = Motif.objects.get_or_create(
            name="Ромб",
            defaults={
                "meaning_description": "Тестовий мотив (dev-seed).",
                "geometry_parameters": {
                    "base_points": [[2.5, 0], [0, 2.5], [2.5, 5]],
                    "symmetry": "reflection_vertical",
                    "params": {},
                },
                "verification_status": Motif.VerificationStatus.VERIFIED,
            },
        )
        diamond.sources.add(source)
        diamond.compatible_regions.add(region)

        wave, _ = Motif.objects.get_or_create(
            name="Хвиля",
            defaults={
                "meaning_description": "Тестовий мотив (dev-seed).",
                "geometry_parameters": {
                    "base_points": [[0, 0], [5, 5], [10, 0]],
                    "symmetry": "wallpaper_p1_horizontal",
                    "params": {"step": 15, "repeats": 4},
                },
                "verification_status": Motif.VerificationStatus.VERIFIED,
            },
        )
        wave.sources.add(source)
        wave.compatible_regions.add(region)

        self.stdout.write(self.style.SUCCESS("Dev-seed дані готові."))
