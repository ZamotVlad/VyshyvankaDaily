from django.core.management.base import BaseCommand
from django.db import transaction

from apps.patterns.models import DailyPattern
from apps.patterns.services.generation import CURRENT_ALGORITHM_VERSION
from apps.patterns.services.pattern_builder import build_svg_for_date


class Command(BaseCommand):
    help = (
        "Перемалювати збережені орнаменти старших версій алгоритму поточною версією. "
        "Дата, регіон і збереження користувачів лишаються; змінюється лише SVG."
    )

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true", help="Лише показати кількість.")

    def handle(self, *args, dry_run=False, **options):
        stale = DailyPattern.objects.filter(
            algorithm_version__lt=CURRENT_ALGORITHM_VERSION,
            generation_status=DailyPattern.GenerationStatus.SUCCESS,
        ).select_related("region")
        total = stale.count()
        if dry_run:
            self.stdout.write(f"До перемальовування: {total}")
            return

        done = failed = 0
        for pattern in stale.iterator():
            try:
                svg, motifs = build_svg_for_date(pattern.date, pattern.region)
            except ValueError as exc:
                failed += 1
                self.stderr.write(f"{pattern.date}: {exc}")
                continue
            with transaction.atomic():
                pattern.svg_content = svg
                pattern.algorithm_version = CURRENT_ALGORITHM_VERSION
                pattern.save(update_fields=["svg_content", "algorithm_version", "updated_at"])
                pattern.motifs_used.set(motifs)
            done += 1
        self.stdout.write(self.style.SUCCESS(f"Перемальовано: {done}, помилок: {failed}"))
