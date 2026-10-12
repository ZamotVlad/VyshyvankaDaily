import hashlib
import json

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from apps.blog.models import Author, BlogCategory, BlogPost
from apps.core.indexnow import bilingual_urls, submit

TEXT_FIELDS = (
    "title",
    "excerpt",
    "seo_title",
    "seo_description",
    "target_keyword",
    "cover_image_alt",
)


def _ping(command, urls):
    if not urls or not settings.INDEXNOW_KEY:
        return
    status = submit(urls)
    command.stdout.write(f"IndexNow: {len(urls)} адрес, відповідь {status}")


def _snapshot(post):
    fields = ["blog_author_id", "category_id", "status", "cover_image_url", "body", "body_en"]
    fields += [f"{f}_{lang}" for f in TEXT_FIELDS for lang in ("uk", "en")]
    return {f: getattr(post, f) for f in fields}


def _digest(value):
    return hashlib.sha256((value or "").encode("utf-8")).hexdigest()[:12]


class Command(BaseCommand):
    help = "Створює або оновлює статті блогу (uk + en) з JSON-файлу, за slug."

    def add_arguments(self, parser):
        parser.add_argument("json_path", type=str, help="Шлях до blog_posts.json")
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Показати, що буде змінено, нічого не зберігаючи в базу.",
        )

    def handle(self, *args, **options):
        try:
            with open(options["json_path"], encoding="utf-8") as f:
                entries = json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            raise CommandError(f"Не вдалося прочитати файл: {exc}") from exc

        dry_run = options["dry_run"]
        self.changed = []
        with transaction.atomic():
            for entry in entries:
                self._load(entry)
            if dry_run:
                transaction.set_rollback(True)
        if dry_run:
            self.stdout.write(self.style.WARNING("Dry-run: нічого не збережено."))
        else:
            _ping(self, self.changed)

    def _load(self, entry):
        author = Author.objects.filter(name_uk=entry["author_name_uk"]).first()
        if author is None:
            raise CommandError(f"Автора не знайдено: {entry['author_name_uk']}")

        cat = entry["category"]
        category, cat_created = BlogCategory.objects.get_or_create(
            slug=cat["slug"],
            defaults={"name_uk": cat["name_uk"], "name_en": cat["name_en"]},
        )

        post = BlogPost.objects.filter(slug=entry["slug"]).first()
        created = post is None
        if created:
            post = BlogPost(slug=entry["slug"])
        before = None if created else _snapshot(post)

        post.blog_author = author
        post.category = category
        post.status = entry["status"]
        post.cover_image_url = entry.get("cover_image_url", "")
        for lang in ("uk", "en"):
            for field in TEXT_FIELDS:
                setattr(post, f"{field}_{lang}", entry[lang].get(field, ""))
        post.body = entry["uk"]["body"]
        post.body_en = entry["en"]["body"]
        if post.status == BlogPost.Status.PUBLISHED and not post.published_at:
            post.published_at = timezone.now()
        # без змін не зберігаємо, щоб updated_at (дата «Оновлено») лишалась чесною
        if created or _snapshot(post) != before:
            post.save()
            label = "створено" if created else "оновлено"
            if post.status == BlogPost.Status.PUBLISHED:
                self.changed += bilingual_urls("blog:detail", post.slug)
        else:
            label = "без змін"
        extra = ", нова категорія" if cat_created else ""
        self.stdout.write(
            f"  [OK] {post.slug}: {label}{extra}; "
            f"uk {_digest(post.body)}, en {_digest(post.body_en)}"
        )
