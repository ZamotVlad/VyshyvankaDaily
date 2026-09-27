from django.conf import settings
from django.urls import translate_url


def seo(request):
    """
    SEO-контекст, доступний у кожному шаблоні: canonical URL (без
    query-параметрів фільтрів, крім валідного номера сторінки > 1) і
    hreflang-посилання на всі мовні версії сторінки + x-default.
    """
    canonical_url = request.build_absolute_uri(request.path)
    page = request.GET.get("page", "")
    if page.isdigit() and int(page) > 1:
        canonical_url = f"{canonical_url}?page={page}"

    hreflang_links = []
    lang_paths = {}
    try:
        for code, _ in settings.LANGUAGES:
            lang_paths[code] = translate_url(request.path, code)
            hreflang_links.append((code, request.build_absolute_uri(lang_paths[code])))
    except Exception:
        hreflang_links = []
        lang_paths = {}
    if hreflang_links:
        hreflang_links.append(("x-default", dict(hreflang_links)[settings.LANGUAGE_CODE]))

    return {
        "canonical_url": canonical_url,
        "hreflang_links": hreflang_links,
        "lang_paths": lang_paths,
        "site_version": settings.SITE_VERSION,
    }
