import json

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.patterns.models import Region

# Ключ у JSON -> поле моделі (без мовного суфікса).
FIELDS = {
    "target_keyword": "target_keyword",
    "seo_title": "seo_title",
    "seo_description": "seo_description",
    "symbolism_description_html": "symbolism_description",
}


class Command(BaseCommand):
    help = "Заповнює SEO-поля та символіку регіонів (uk + en) з JSON-файлу."

    def add_arguments(self, parser):
        parser.add_argument("json_path", type=str, help="Шлях до region_content.json")
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Показати, що буде змінено, нічого не зберігаючи в базу.",
        )
        parser.add_argument(
            "--check",
            action="store_true",
            help="Лише показати регіони, де українські тексти в базі відрізняються від файлу.",
        )

    def handle(self, *args, **options):
        entries = self._read(options["json_path"])
        self.stdout.write(f"У файлі {len(entries)} регіонів.")

        if options["check"]:
            self._check(entries)
            return

        dry_run = options["dry_run"]
        updated, not_found = [], []
        with transaction.atomic():
            for entry in entries:
                region = Region.objects.filter(slug=entry["slug"]).first()
                if region is None:
                    not_found.append(entry["slug"])
                    continue
                changed = self._apply(region, entry)
                if not dry_run:
                    region.save()
                label = "[БУЛО Б]" if dry_run else "[OK]"
                self.stdout.write(f"  {label} {region.slug}: {', '.join(changed) or 'без змін'}")
                updated.append(region.slug)
            if dry_run:
                transaction.set_rollback(True)

        verb = "Було б оновлено" if dry_run else "Оновлено"
        self.stdout.write(self.style.SUCCESS(f"\n{verb}: {len(updated)} регіонів."))
        if not_found:
            self.stdout.write(self.style.ERROR(f"Не знайдено в базі: {', '.join(not_found)}"))
        if dry_run:
            self.stdout.write(self.style.WARNING("Це був --dry-run, у базу нічого не записано."))

    def _read(self, path):
        try:
            with open(path, encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError as exc:
            raise CommandError(f"Файл не знайдено: {path}") from exc
        except json.JSONDecodeError as exc:
            raise CommandError(f"Файл не є коректним JSON: {exc}") from exc

    def _values(self, entry):
        """(поле_з_мовою, значення) для uk та, якщо є, en."""
        for key, field in FIELDS.items():
            if key in entry:
                yield f"{field}_uk", entry[key]
            if key in entry.get("en", {}):
                yield f"{field}_en", entry["en"][key]

    def _apply(self, region, entry):
        changed = []
        for field, value in self._values(entry):
            if (getattr(region, field) or "") != value:
                setattr(region, field, value)
                changed.append(field)
        return changed

    def _check(self, entries):
        differ = []
        for entry in entries:
            region = Region.objects.filter(slug=entry["slug"]).first()
            if region is None:
                self.stdout.write(self.style.ERROR(f"  {entry['slug']}: немає в базі"))
                continue
            fields = [
                field
                for field, value in self._values(entry)
                if field.endswith("_uk") and (getattr(region, field) or "") != value
            ]
            if fields:
                differ.append(region.slug)
                self.stdout.write(f"  {region.slug}: відрізняється {', '.join(fields)}")
        if differ:
            self.stdout.write(
                self.style.WARNING(f"\nУ базі інші тексти для {len(differ)} регіонів.")
            )
        else:
            self.stdout.write(self.style.SUCCESS("Українські тексти в базі збігаються з файлом."))
