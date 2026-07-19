from django.shortcuts import get_object_or_404, render

from .models import FAQCategory, StaticPage


def about_view(request):
    return render(request, "pages/about.html")


def terms_view(request):
    return render(request, "pages/terms.html")


def privacy_view(request):
    return render(request, "pages/privacy.html")


def contacts_view(request):
    """
    Статична сторінка (свідоме відхилення від розділу 5.11 ТЗ,
    задокументоване в Частині 2 DECISIONS.md) — соло-розробка, особистий
    email зручніший за форму+адмінку для очікуваного обсягу звернень.
    """
    return render(request, "pages/contact.html")


def static_page_view(request, slug):
    page = get_object_or_404(StaticPage, slug=slug)
    return render(request, "pages/static_page.html", {"page": page})


def faq_view(request):
    categories = FAQCategory.objects.prefetch_related("items").order_by("order")
    return render(request, "pages/faq.html", {"categories": categories})
