from django.urls import translate_url
from django.utils import translation


def seo(request):
    """
    SEO-контекст, доступний у кожному шаблоні: canonical URL (без
    query-параметрів фільтрів/пагінації, крім самого page) і посилання
    на цю саму сторінку іншою мовою (для hreflang у <head>).
    """
    canonical_path = request.path
    page = request.GET.get("page")
    canonical_url = request.build_absolute_uri(canonical_path)
    if page:
        canonical_url = f"{canonical_url}?page={page}"

    other_lang = "en" if translation.get_language() == "uk" else "uk"
    try:
        alternate_url = request.build_absolute_uri(translate_url(request.path, other_lang))
    except Exception:
        alternate_url = None

    return {
        "canonical_url": canonical_url,
        "alternate_lang_code": other_lang,
        "alternate_url": alternate_url,
    }
