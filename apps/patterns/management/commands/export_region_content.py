import json

from django.core.management.base import BaseCommand

from apps.patterns.models import Region

from .load_region_content import FIELDS


class Command(BaseCommand):
    help = "Тексти регіонів у форматі region_content.json (лише ASCII)."

    def add_arguments(self, parser):
        parser.add_argument("slugs", nargs="*", help="Slug регіонів; без аргументів - усі.")

    def handle(self, *args, **options):
        regions = Region.objects.order_by("rotation_order", "pk")
        if options["slugs"]:
            regions = regions.filter(slug__in=options["slugs"])

        entries = []
        for region in regions:
            entry = {"slug": region.slug}
            en = {}
            for key, field in FIELDS.items():
                entry[key] = getattr(region, f"{field}_uk") or ""
                if getattr(region, f"{field}_en"):
                    en[key] = getattr(region, f"{field}_en")
            if en:
                entry["en"] = en
            entries.append(entry)

        self.stdout.write(json.dumps(entries, ensure_ascii=True, indent=2))
