from django.shortcuts import get_object_or_404, render

from .models import FAQCategory, StaticPage


def about_view(request):
    return render(request, "pages/about.html")


def sources_view(request):
    return render(request, "pages/sources.html")


def terms_view(request):
    return render(request, "pages/terms.html")


def privacy_view(request):
    return render(request, "pages/privacy.html")


def contacts_view(request):
    """
    Статична сторінка без форми: для очікуваного обсягу звернень
    пошта зручніша за форму й адмінку.
    """
    return render(request, "pages/contact.html")


def static_page_view(request, slug):
    page = get_object_or_404(StaticPage, slug=slug)
    return render(request, "pages/static_page.html", {"page": page})


def faq_view(request):
    categories = FAQCategory.objects.prefetch_related("items").order_by("order")
    return render(request, "pages/faq.html", {"categories": categories})
