from django.contrib.syndication.views import Feed
from django.urls import reverse

from .models import BlogPost


class BlogFeed(Feed):
    title = "VyshyvankaDaily - блог"
    description = "Дослідження, символіка, історії регіонів."

    def link(self):
        return reverse("blog:list")

    def items(self):
        return BlogPost.objects.filter(status="published").order_by("-published_at")[:20]

    def item_title(self, item):
        return item.title

    def item_description(self, item):
        return getattr(item, "excerpt", "") or ""

    def item_link(self, item):
        return reverse("blog:detail", args=[item.slug])

    def item_pubdate(self, item):
        return getattr(item, "published_at", None)
