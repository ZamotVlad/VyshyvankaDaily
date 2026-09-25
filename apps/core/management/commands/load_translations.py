import json

from django.apps import apps
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.core.translations import TARGETS, digest


class Command(BaseCommand):
    help = (
        "Заповнює EN-поля FAQ, мотивів і авторів з JSON. Об'єкт шукається за "
        "українським текстом; якщо він у базі інший, переклад не застосовується."
    )

    def add_arguments(self, parser):
        parser.add_argument("json_path")
        parser.add_argument("--dry-run", action="store_true", help="Нічого не зберігати.")
        parser.add_argument(
            "--check", action="store_true", help="Лише звірити українські тексти з базою."
        )

    def handle(self, *args, **options):
        try:
            with open(options["json_path"], encoding="utf-8") as f:
                entries = json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            raise CommandError(f"Не вдалося прочитати файл: {exc}") from exc

        write = not (options["check"] or options["dry_run"])
        counts = {"ok": 0, "changed": 0, "skipped": 0}
        with transaction.atomic():
            for entry in entries:
                self._process(entry, write, options["check"], counts)
            if not write:
                transaction.set_rollback(True)

        summary = f"\nЗбіглося: {counts['ok']}, пропущено: {counts['skipped']}"
        if not options["check"]:
            verb = "оновлено" if write else "було б оновлено"
            summary += f", {verb}: {counts['changed']}"
        self.stdout.write(summary + ".")
        if counts["skipped"]:
            self.stdout.write(self.style.WARNING("Пропущені тексти в базі інші, ніж у файлі."))

    def _process(self, entry, write, check_only, counts):
        label = entry["model"]
        if label not in TARGETS:
            raise CommandError(f"Невідома модель: {label}")
        model = apps.get_model(label)
        uk = entry["uk"]
        first = TARGETS[label][0]
        title = f"{label} (текст {digest(uk[first])})"

        matches = list(model.objects.filter(**{f"{f}_uk": v for f, v in uk.items()}))
        if not matches:
            counts["skipped"] += 1
            by_first = model.objects.filter(**{f"{first}_uk": uk[first]}).first()
            if by_first is None:
                self.stdout.write(self.style.ERROR(f"  {title}: немає в базі"))
            else:
                diff = [
                    f"{f} (база {digest(getattr(by_first, f'{f}_uk'))})"
                    for f, v in uk.items()
                    if (getattr(by_first, f"{f}_uk") or "") != v
                ]
                self.stdout.write(f"  {title}: відрізняється {', '.join(diff)}")
            return

        counts["ok"] += 1
        if check_only:
            return
        for obj in matches:
            changed = [f for f, v in entry.get("en", {}).items() if getattr(obj, f"{f}_en") != v]
            for f in changed:
                setattr(obj, f"{f}_en", entry["en"][f])
            if changed:
                counts["changed"] += 1
                obj.save()
                self.stdout.write(f"  {title}: {', '.join(f'{f}_en' for f in changed)}")
