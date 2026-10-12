from django.core.management.base import BaseCommand

from apps.core.indexnow import bilingual_urls, submit
from apps.core.sitemaps import StaticViewSitemap


class Command(BaseCommand):
    help = "Надсилає адреси в IndexNow: усі сторінки сайту (--all) або передані адреси."

    def add_arguments(self, parser):
        parser.add_argument("urls", nargs="*")
        parser.add_argument("--all", action="store_true", help="Усі публічні сторінки UA і EN.")

    def handle(self, *args, **options):
        from apps.blog.models import BlogPost
        from apps.patterns.models import Region

        urls = list(options["urls"])
        if options["all"]:
            for name in StaticViewSitemap().items():
                urls += bilingual_urls(name)
            for slug in Region.objects.values_list("slug", flat=True):
                urls += bilingual_urls("patterns:region_detail", slug)
            posts = BlogPost.objects.filter(
                status=BlogPost.Status.PUBLISHED, published_at__isnull=False
            )
            for slug in posts.values_list("slug", flat=True):
                urls += bilingual_urls("blog:detail", slug)
        if not urls:
            self.stdout.write("Немає адрес: передайте їх або --all.")
            return
        status = submit(urls)
        if status is None:
            self.stdout.write(
                self.style.WARNING("Не надіслано: немає INDEXNOW_KEY або помилка мережі.")
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(f"IndexNow: {len(set(urls))} адрес, відповідь {status}.")
            )
