from django.core.management.base import BaseCommand

from apps.patterns.models import DailyPattern
from apps.patterns.services.generation import CURRENT_ALGORITHM_VERSION, retry_fallback_pattern
from apps.patterns.services.pattern_builder import build_svg_for_date


class Command(BaseCommand):
    help = "Перегенерувати дні, де спрацював резервний (fallback) орнамент."

    def handle(self, *args, **options):
        fallbacks = list(
            DailyPattern.objects.filter(
                generation_status=DailyPattern.GenerationStatus.FALLBACK
            ).order_by("date")
        )
        fixed = 0
        for pattern in fallbacks:
            try:
                retry_fallback_pattern(pattern, CURRENT_ALGORITHM_VERSION, build_svg_for_date)
                fixed += 1
                self.stdout.write(f"{pattern.date}: OK ({pattern.region})")
            except Exception as exc:
                self.stderr.write(f"{pattern.date}: помилка - {exc}")
        self.stdout.write(f"Перегенеровано: {fixed} з {len(fallbacks)}")
