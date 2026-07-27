from datetime import datetime
from pathlib import Path

from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Створює JSON-бекап даних, які не відтворюються з міграцій."

    def add_arguments(self, parser):
        parser.add_argument("--output-dir", default="backups")

    def handle(self, *args, **options):
        out_dir = Path(options["output_dir"])
        out_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("%Y-%m-%d_%H%M")

        # Довідники (Region/Motif/Source) свідомо НЕ бекапимо: вони
        # повністю відтворюються з міграцій командою migrate. Бекап
        # потрібен лише для того, що створюють живі люди.
        targets = {
            "users": ["auth.User", "accounts.Profile"],
            "collections": ["patterns.SavedPattern"],
            "patterns": ["patterns.DailyPattern"],
            "blog": ["blog.BlogPost", "blog.BlogCategory", "blog.GuestPostSubmission"],
            "pages": ["pages.FAQCategory", "pages.FAQItem"],
        }

        for name, models in targets.items():
            path = out_dir / f"{stamp}_{name}.json"
            with path.open("w", encoding="utf-8") as handle:
                call_command(
                    "dumpdata",
                    *models,
                    indent=2,
                    stdout=handle,
                    natural_foreign=True,
                    natural_primary=True,
                )
            size_kb = path.stat().st_size / 1024
            self.stdout.write(self.style.SUCCESS(f"{path} ({size_kb:.1f} КБ)"))

        self.stdout.write(
            self.style.WARNING(
                "\nБекап зроблено. Обов'язково скопіюй файли з сервера до себе - "
                "бекап, що лежить на тому самому диску, що й база, не рятує "
                "від відмови цього диска."
            )
        )
