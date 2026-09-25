import json
from datetime import datetime
from io import StringIO
from pathlib import Path

from django.core.management import call_command
from django.core.management.base import BaseCommand

TARGETS = {
    "users": [
        "auth.User",
        "accounts.Profile",
        "account.EmailAddress",
        "socialaccount.SocialAccount",
    ],
    "collections": ["patterns.SavedPattern"],
    "patterns": ["patterns.DailyPattern"],
    "content": [
        "patterns.Source",
        "patterns.Region",
        "patterns.Motif",
        "patterns.RegionPhoto",
        "blog.Author",
        "pages.StaticPage",
    ],
    "blog": ["blog.BlogCategory", "blog.BlogPost", "blog.GuestPostSubmission"],
    "pages": ["pages.FAQCategory", "pages.FAQItem"],
}

# Паролі й IP не потрапляють у файли: "!" - непридатний пароль у Django.
SCRUB = {
    "auth.user": {"password": "!"},
    "blog.guestpostsubmission": {"submitter_ip": None},
}


class Command(BaseCommand):
    help = "JSON-бекап даних сайту без хешів паролів та IP-адрес."

    def add_arguments(self, parser):
        parser.add_argument("--output-dir", default="backups")

    def handle(self, *args, **options):
        out_dir = Path(options["output_dir"])
        out_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("%Y-%m-%d_%H%M")

        for name, models in TARGETS.items():
            buffer = StringIO()
            call_command(
                "dumpdata",
                *models,
                stdout=buffer,
                natural_foreign=True,
                natural_primary=True,
            )
            objects = json.loads(buffer.getvalue())
            for obj in objects:
                obj["fields"].update(SCRUB.get(obj["model"], {}))

            path = out_dir / f"{stamp}_{name}.json"
            path.write_text(json.dumps(objects, ensure_ascii=False, indent=2), encoding="utf-8")
            size_kb = path.stat().st_size / 1024
            self.stdout.write(self.style.SUCCESS(f"{path} ({size_kb:.1f} КБ)"))

        self.stdout.write(
            self.style.WARNING(
                "\nФайли містять email користувачів - зберігай їх приватно, поза репозиторієм."
            )
        )
