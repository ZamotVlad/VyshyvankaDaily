import json

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.patterns.models import Region, RegionPhoto

SOURCE_NOTE = "Ілюстрація VyshyvankaDaily"


def _url(path):
    """Повна адреса на проді (поле URLField), локально - шлях від кореня."""
    host = settings.CANONICAL_HOST
    return f"https://{host}{path}" if host else path


class Command(BaseCommand):
    help = "Синхронізує ілюстрації регіонів (RegionPhoto) з JSON-файлу."

    def add_arguments(self, parser):
        parser.add_argument("json_path", type=str, help="Шлях до region_photos.json")
        parser.add_argument("--dry-run", action="store_true", help="Нічого не зберігати.")

    def handle(self, *args, **options):
        try:
            with open(options["json_path"], encoding="utf-8") as f:
                entries = json.load(f)
        except (OSError, ValueError) as exc:
            raise CommandError(f"Не вдалося прочитати файл: {exc}") from exc

        dry_run = options["dry_run"]
        created, updated, removed, missing = 0, 0, 0, set()
        with transaction.atomic():
            listed = {}
            for entry in entries:
                region = Region.objects.filter(slug=entry["region"]).first()
                if region is None:
                    missing.add(entry["region"])
                    continue
                image = _url(entry["image"])
                listed.setdefault(region.pk, set()).add(image)
                values = {
                    "thumbnail_url": _url(entry["thumbnail"]),
                    "caption_uk": entry["caption_uk"],
                    "caption_en": entry["caption_en"],
                    "source_note": SOURCE_NOTE,
                    "order": entry.get("order", 0),
                    "is_active": True,
                }
                photo = RegionPhoto.objects.filter(region=region, image_url=image).first()
                if photo is None:
                    created += 1
                    if not dry_run:
                        RegionPhoto.objects.create(region=region, image_url=image, **values)
                    continue
                changed = [k for k, v in values.items() if getattr(photo, k) != v]
                if changed:
                    updated += 1
                    if not dry_run:
                        for k in changed:
                            setattr(photo, k, values[k])
                        photo.save()
            # Видаляємо лише власні ілюстрації, яких немає у файлі; справжні фото лишаються.
            stale = RegionPhoto.objects.filter(source_note=SOURCE_NOTE)
            for photo in stale:
                if photo.image_url not in listed.get(photo.region_id, set()):
                    removed += 1
                    if not dry_run:
                        photo.delete()
            if dry_run:
                transaction.set_rollback(True)

        for slug in sorted(missing):
            self.stdout.write(self.style.WARNING(f"  Регіон не знайдено: {slug}"))
        verb = "Було б" if dry_run else "Готово:"
        self.stdout.write(
            f"{verb} створено {created}, оновлено {updated}, видалено {removed}."
            + (" Це був --dry-run." if dry_run else "")
        )
