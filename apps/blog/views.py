from django.contrib import messages
from django.core.paginator import Paginator
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django_ratelimit.decorators import ratelimit

from apps.blog.forms import GuestPostSubmissionForm
from apps.blog.models import BlogCategory, BlogPost

BLOG_PAGE_SIZE = 12


def blog_list_view(request):
    posts = BlogPost.objects.filter(status=BlogPost.Status.PUBLISHED).select_related("category")

    category_slug = request.GET.get("category", "")
    if category_slug:
        category = BlogCategory.objects.filter(slug=category_slug, is_active=True).first()
        if category is not None:
            posts = posts.filter(category=category)

    paginator = Paginator(posts, BLOG_PAGE_SIZE)
    page_obj = paginator.get_page(request.GET.get("page"))

    context = {
        "page_obj": page_obj,
        "categories": BlogCategory.objects.filter(is_active=True).order_by("name"),
        "selected_category_slug": category_slug,
    }
    return render(request, "blog/blog_list.html", context)


def blog_detail_view(request, slug):
    post = get_object_or_404(BlogPost.objects.select_related("category"), slug=slug)

    if post.status == BlogPost.Status.DRAFT and not request.user.is_staff:
        raise Http404

    related_posts = (
        BlogPost.objects.filter(status=BlogPost.Status.PUBLISHED, category=post.category)
        .exclude(pk=post.pk)
        .order_by("-published_at")[:3]
    )

    context = {
        "post": post,
        "related_posts": related_posts,
        "is_partner_content": post.post_type != BlogPost.PostType.EDITORIAL,
    }
    return render(request, "blog/blog_detail.html", context)


@ratelimit(key="ip", rate="3/h", block=True)
@ratelimit(key="post:email", rate="3/h", block=True)
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
                submission.submitter_ip = request.META.get("REMOTE_ADDR")
                submission.save()
            messages.success(request, "Дякуємо! Заявку отримано.")
            return redirect("blog:propose")
    else:
        form = GuestPostSubmissionForm()

    return render(request, "blog/guest_post_propose.html", {"form": form})
