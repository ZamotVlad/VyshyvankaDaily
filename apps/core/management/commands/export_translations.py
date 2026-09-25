import json

from django.apps import apps
from django.core.management.base import BaseCommand, CommandError

from apps.core.translations import TARGETS


class Command(BaseCommand):
    help = "Тексти uk/en для FAQ, мотивів і авторів у JSON (лише ASCII)."

    def add_arguments(self, parser):
        parser.add_argument("models", nargs="*", help=f"Моделі: {', '.join(TARGETS)}")

    def handle(self, *args, **options):
        labels = options["models"] or list(TARGETS)
        unknown = set(labels) - set(TARGETS)
        if unknown:
            raise CommandError(f"Невідомі моделі: {', '.join(sorted(unknown))}")

        entries = []
        for label in labels:
            fields = TARGETS[label]
            for obj in apps.get_model(label).objects.order_by("pk"):
                entries.append(
                    {
                        "model": label,
                        "uk": {f: getattr(obj, f"{f}_uk") or "" for f in fields},
                        "en": {f: getattr(obj, f"{f}_en") or "" for f in fields},
                    }
                )
        self.stdout.write(json.dumps(entries, ensure_ascii=True, indent=2))
