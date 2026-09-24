import json

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.patterns.models import Region


class Command(BaseCommand):
    help = "Заповнює SEO-поля та symbolism_description для регіонів з JSON-файлу."

    def add_arguments(self, parser):
        parser.add_argument(
            "json_path",
            type=str,
            help="Шлях до region_content.json",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Показати, що буде змінено, нічого не зберігаючи в базу.",
        )

    def handle(self, *args, **options):
        json_path = options["json_path"]
        dry_run = options["dry_run"]

        try:
            with open(json_path, encoding="utf-8") as f:
                entries = json.load(f)
        except FileNotFoundError as exc:
            raise CommandError(f"Файл не знайдено: {json_path}") from exc
        except json.JSONDecodeError as exc:
            raise CommandError(f"Файл не є коректним JSON: {exc}") from exc

        self.stdout.write(f"У файлі {len(entries)} регіонів.")

        updated = []
        not_found = []

        with transaction.atomic():
            for entry in entries:
                slug = entry["slug"]
                try:
                    region = Region.objects.get(slug=slug)
                except Region.DoesNotExist:
                    not_found.append(slug)
                    continue

                old_len = len(region.symbolism_description or "")

                region.target_keyword_uk = entry["target_keyword"]
                region.seo_title_uk = entry["seo_title"]
                region.seo_description_uk = entry["seo_description"]
                region.symbolism_description = entry["symbolism_description_html"]

                new_len = len(entry["symbolism_description_html"])

                if dry_run:
                    self.stdout.write(
                        f"  [БУЛО Б] {slug}: символіка {old_len} -> {new_len} символів, "
                        f"keyword='{entry['target_keyword']}'"
                    )
                else:
                    region.save()
                    self.stdout.write(f"  [OK] {slug}: символіка {old_len} -> {new_len} символів")

                updated.append(slug)

            if dry_run:
                # відкат навіть якщо хтось у циклі помилково викликав save()
                transaction.set_rollback(True)

        self.stdout.write("")
        self.stdout.write(
            self.style.SUCCESS(
                f"{'Було б оновлено' if dry_run else 'Оновлено'}: {len(updated)} регіонів."
            )
        )
        if not_found:
            self.stdout.write(
                self.style.ERROR(f"Не знайдено в базі (перевір slug): {', '.join(not_found)}")
            )
        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    "Це був --dry-run, у базу нічого не записано. "
                    "Прибери --dry-run, щоб застосувати справді."
                )
            )
