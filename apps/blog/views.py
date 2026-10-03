import re

from django.contrib import messages
from django.core.paginator import Paginator
from django.db import models
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext as _
from django_ratelimit.decorators import ratelimit

from apps.blog.forms import GuestPostSubmissionForm
from apps.blog.models import Author, BlogCategory, BlogPost
from apps.core.toc import build_toc
from apps.core.utils import client_ip

BLOG_PAGE_SIZE = 12


def author_detail_view(request, slug):
    from apps.patterns.models import Region

    author = get_object_or_404(Author, slug=slug)
    posts = (
        BlogPost.objects.filter(status=BlogPost.Status.PUBLISHED, blog_author=author)
        .select_related("category")
        .order_by("-published_at")
    )
    regions = Region.objects.verified().order_by("name")
    return render(
        request,
        "blog/author_detail.html",
        {"author": author, "posts": posts, "regions": regions},
    )


def blog_list_view(request):
    posts = BlogPost.objects.filter(status=BlogPost.Status.PUBLISHED).select_related("category")

    category_slug = request.GET.get("category", "")
    if category_slug:
        category = BlogCategory.objects.filter(slug=category_slug, is_active=True).first()
        if category is not None:
            posts = posts.filter(category=category)

    query = request.GET.get("q", "").strip()
    if query:
        posts = posts.filter(models.Q(title__icontains=query) | models.Q(excerpt__icontains=query))

    paginator = Paginator(posts, BLOG_PAGE_SIZE)
    page_obj = paginator.get_page(request.GET.get("page"))

    context = {
        "page_obj": page_obj,
        "categories": BlogCategory.objects.filter(is_active=True).order_by("name"),
        "selected_category_slug": category_slug,
        "query": query,
    }
    return render(request, "blog/blog_list.html", context)


def _mentioned_regions(post, body):
    """Регіони, на які посилається стаття, у порядку згадки (+ прив'язаний регіон)."""
    from apps.patterns.models import Region

    slugs = re.findall(r'href="(?:/en)?/regions/([a-z0-9-]+)/"', body)
    if post.related_region_id:
        slugs.insert(0, post.related_region.slug)
    slugs = list(dict.fromkeys(slugs))
    regions = {r.slug: r for r in Region.objects.filter(slug__in=slugs)}
    return [regions[slug] for slug in slugs if slug in regions]


def blog_detail_view(request, slug):
    post = get_object_or_404(BlogPost.objects.select_related("category"), slug=slug)

    if post.status == BlogPost.Status.DRAFT and not request.user.is_staff:
        raise Http404

    related_posts = (
        BlogPost.objects.filter(status=BlogPost.Status.PUBLISHED, category=post.category)
        .exclude(pk=post.pk)
        .order_by("-published_at")[:3]
    )

    body, toc = build_toc(post.localized_body, reserved=("sources", "regions"))
    if post.sources.exists():
        toc.append({"id": "sources", "title": _("Джерела")})
    mentioned_regions = _mentioned_regions(post, body)
    if mentioned_regions:
        toc.append({"id": "regions", "title": _("Регіони в цій статті")})

    context = {
        "post": post,
        "body": body,
        "toc": toc,
        "mentioned_regions": mentioned_regions,
        "related_posts": related_posts,
        "is_partner_content": post.post_type != BlogPost.PostType.EDITORIAL,
    }
    return render(request, "blog/blog_detail.html", context)


@ratelimit(key="ip", rate="3/h", method="POST", block=True)
@ratelimit(key="post:email", rate="3/h", method="POST", block=True)
def guest_post_propose_view(request):
    """
    Заявка на гостьовий пост (розділ 5.12, 6.4, 13.1 ТЗ).

    Ключ обмеження — IP-адреса ТА email одночасно (розділ 13.1, таблиця):
    два незалежні декоратори, кожен блокує самостійно — заблокує, якщо
    перевищено ліміт за будь-яким із двох вимірів. Підтверджено офіційною
    документацією django-ratelimit ("Use multiple keys by stacking
    decorators").

    Honeypot: якщо приховане поле заповнене (бот), тихо не зберігаємо
    заявку, але показуємо той самий "успіх" — не видаємо боту, що його
    спіймано.
    """
    if request.method == "POST":
        form = GuestPostSubmissionForm(request.POST)
        if form.is_valid():
            if not form.cleaned_data.get("honeypot"):
                submission = form.save(commit=False)
                submission.submitter_ip = client_ip(request)
                submission.save()
            messages.success(request, _("Дякуємо! Заявку отримано."))
            return redirect("blog:propose")
    else:
        form = GuestPostSubmissionForm()

    return render(request, "blog/guest_post_propose.html", {"form": form})
