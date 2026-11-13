import difflib
import re
from datetime import timedelta

from django.conf import settings
from django.http import Http404, HttpResponse, HttpResponsePermanentRedirect, HttpResponseRedirect
from django.shortcuts import render
from django.templatetags.static import static
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.utils.translation import check_for_language
from django.views.decorators.cache import cache_page

# Префікси НЕ-дефолтних мов (де prefix_default_language=False - українська
# без префіксу, решта з ним). Зараз лише "en", але список сам розшириться,
# якщо колись додасться третя мова.
_NON_DEFAULT_PREFIXES = [code for code, _ in settings.LANGUAGES if code != settings.LANGUAGE_CODE]
_PREFIX_RE = re.compile(rf"^/({'|'.join(_NON_DEFAULT_PREFIXES)})(/|$)")


def set_language_view(request):
    """
    Заміна вбудованого django.views.i18n.set_language.

    Причина: відомий, задокументований баг Django (тікети #26556, #28567) -
    set_language() намагається "перекласти" next-URL у нову мову через
    translate_url(), але це не працює коректно, коли
    prefix_default_language=False (наш випадок - українська без префіксу).
    Результат багу: перемикання назад на дефолтну мову залишає старий
    префікс (/en/) у Location, і сторінка "не перемикається".

    Це виправлення просто знімає будь-який мовний префікс з next вручну,
    і додає правильний префікс для НОВОЇ мови (чи не додає - для дефолтної).
    """
    lang_code = request.POST.get("language")
    next_url = request.POST.get("next") or request.META.get("HTTP_REFERER") or "/"

    # Прибрати домен, якщо referer - повний URL
    if next_url.startswith("http"):
        from urllib.parse import urlparse

        next_url = urlparse(next_url).path or "/"

    # Зняти наявний мовний префікс (якщо він там є)
    stripped = _PREFIX_RE.sub("/", next_url, count=1)
    if not stripped.startswith("/"):
        stripped = "/" + stripped
    if not url_has_allowed_host_and_scheme(stripped, allowed_hosts={request.get_host()}):
        stripped = "/"

    if lang_code and check_for_language(lang_code):
        if lang_code != settings.LANGUAGE_CODE:
            next_url = f"/{lang_code}{stripped}"
        else:
            next_url = stripped
    else:
        next_url = stripped

    response = HttpResponseRedirect(next_url)
    if lang_code and check_for_language(lang_code):
        response.set_cookie(
            settings.LANGUAGE_COOKIE_NAME,
            lang_code,
            max_age=settings.LANGUAGE_COOKIE_AGE,
            path=settings.LANGUAGE_COOKIE_PATH,
            domain=settings.LANGUAGE_COOKIE_DOMAIN,
            secure=settings.LANGUAGE_COOKIE_SECURE,
            httponly=settings.LANGUAGE_COOKIE_HTTPONLY,
            samesite=settings.LANGUAGE_COOKIE_SAMESITE,
        )
    return response


def robots_txt(request):
    """
    Disallow лише для приватного й внутрішнього пошуку блогу.

    Сторінки днів (/pattern/) і фільтри блогу (?category=) відкриті для
    сканування: робот має побачити на них noindex або canonical, інакше
    вже проіндексовані адреси не зникнуть з видачі.
    """
    private = ["/accounts/", "/profile/settings/", "/collection/", "/patterns/debug/"]
    lines = [
        "User-agent: *",
        *(f"Disallow: {prefix}{path}" for path in private for prefix in ("", "/en")),
        *(f"Disallow: {prefix}/blog/?q=" for prefix in ("", "/en")),
        "",
        f"Sitemap: {request.scheme}://{request.get_host()}/sitemap.xml",
    ]
    return HttpResponse("\n".join(lines), content_type="text/plain")


def security_txt(request):
    """RFC 9116: контакт для повідомлень про вразливості."""
    expires = timezone.now() + timedelta(days=180)
    lines = [
        "Contact: mailto:vyshyvankadaily@gmail.com",
        f"Expires: {expires.strftime('%Y-%m-%dT00:00:00Z')}",
        "Preferred-Languages: uk, en",
        f"Canonical: {request.scheme}://{request.get_host()}/.well-known/security.txt",
    ]
    return HttpResponse("\n".join(lines) + "\n", content_type="text/plain")


def google_site_verification(request):
    """
    Файл підтвердження власності домену для Google Search Console.
    Обслуговується через view, а не фізичний файл на диску, бо файлова
    система Heroku ефемерна - будь-що, не закомічене в git, зникає
    при кожному новому деплої.
    """
    return HttpResponse(
        "google-site-verification: googled602211b36b6f933.html",
        content_type="text/plain",
    )


def csrf_failure(request, reason=""):
    """
    Власний обробник CSRF-відмов (Django за замовчуванням показує
    негарну вбудовану сторінку). Це НЕ вразливість - навпаки, захист
    відхилив застарілий/невідповідний токен, як і мав. Найчастіша
    причина: форма була відкрита довго, чи натиснута кнопка "назад".
    """
    return render(request, "403_csrf.html", {"reason": reason}, status=403)


def favicon(request):
    return HttpResponsePermanentRedirect(static("favicon/favicon.png"))


def _plain_description(text):
    """SEO-опис без закликів на кшталт «- читайте на VyshyvankaDaily!»."""
    text = re.sub(r"\s+-\s+(читайте |дивіться )?[^-.!?]*VyshyvankaDaily!?\s*$", "", text or "")
    sentences = re.split(r"(?<=[.!?])\s+", text)
    return " ".join(s for s in sentences if "VyshyvankaDaily" not in s).strip()


def _post_dates(post):
    """Дати статті для AI: опубліковано і, якщо була правка пізніше, оновлено."""
    text = f"опубліковано {post.published_at:%Y-%m-%d}"
    if post.updated_at.date() > post.published_at.date():
        text += f", оновлено {post.updated_at:%Y-%m-%d}"
    return text


def _source_line(source):
    line = f"- {source.name}"
    if source.author_or_institution:
        line += f" - {source.author_or_institution}"
    if source.publication_year:
        line += f" ({source.publication_year})"
    return line


def llms_txt(request):
    """Опис сайту для AI-пошуку (llmstxt.org): що це, регіони, статті."""
    from apps.blog.models import BlogPost
    from apps.patterns.models import Region

    base = f"{request.scheme}://{request.get_host()}"
    regions = list(Region.objects.order_by("name_uk"))
    posts = list(
        BlogPost.objects.filter(status=BlogPost.Status.PUBLISHED, published_at__isnull=False)
    )
    lines = [
        "# VyshyvankaDaily",
        "",
        "> Орнаменти української вишивки 27 регіонів України: символіка, кольори, техніки й "
        "перевірені джерела (музеї, наукові видання), а також статті про вишиванку, рушники "
        "й українську культуру. Двомовний сайт: українська (основна) і англійська (/en/).",
        "",
        "> Ornaments of Ukrainian embroidery from 27 regions of Ukraine: symbolism, colours, "
        "techniques and verified sources (museums, academic publications), plus articles on the "
        "vyshyvanka, rushnyky and Ukrainian culture. English version under /en/.",
        "",
        "## Головне / Main",
        f"- [Орнамент дня / Ornament of the day]({base}/): щодня новий орнамент одного з регіонів",
        f"- [Вишиванки по регіонах]({base}/regions/) / [Regions]({base}/en/regions/)",
        f"- [Символи на вишиванці]({base}/symbols/) / [Ukrainian embroidery symbols]"
        f"({base}/en/symbols/): значення ромба, хреста, зірки, дерева життя й інших мотивів",
        f"- [Блог]({base}/blog/) / [Blog]({base}/en/blog/)",
        f"- [Як ми працюємо з джерелами]({base}/sources/) / [How we work with sources]"
        f"({base}/en/sources/): рівні джерел, тлумачення, кольори, зображення, виправлення",
        f"- [Повні тексти для AI / Full texts]({base}/llms-full.txt)",
        "",
        "## Регіони / Regions",
    ]
    for r in regions:
        desc = _plain_description(r.seo_description_uk)
        lines.append(
            f"- [{r.name_uk}]({base}/regions/{r.slug}/) / [{r.name_en or r.name_uk}]"
            f"({base}/en/regions/{r.slug}/)" + (f": {desc}" if desc else "")
        )
    if posts:
        lines += ["", "## Статті / Articles"]
        for post in posts:
            desc = _plain_description(post.seo_description_uk or post.excerpt_uk)
            en = f" / [{post.title_en}]({base}/en/blog/{post.slug}/)" if post.title_en else ""
            notes = " ".join(x for x in (desc, f"({_post_dates(post)})") if x)
            lines.append(f"- [{post.title_uk}]({base}/blog/{post.slug}/){en}: {notes}")
    lines += [
        "",
        "## Optional",
        f"- [Часті питання]({base}/faq/) / [FAQ]({base}/en/faq/)",
        f"- [Про проєкт]({base}/about/) / [About]({base}/en/about/)",
        "",
    ]
    return HttpResponse("\n".join(lines), content_type="text/plain; charset=utf-8")


def indexnow_key(request, key):
    """Файл ключа IndexNow: /<ключ>.txt з тим самим ключем усередині."""
    if not settings.INDEXNOW_KEY or key != settings.INDEXNOW_KEY:
        raise Http404
    return HttpResponse(key, content_type="text/plain; charset=utf-8")


@cache_page(60 * 60)
def llms_full_txt(request):
    """Повні тексти регіонів і статей обома мовами для AI-систем (llmstxt.org)."""
    from apps.blog.models import BlogPost
    from apps.core.llms import html_to_markdown
    from apps.patterns.models import Region

    base = f"{request.scheme}://{request.get_host()}"
    regions = list(Region.objects.prefetch_related("sources").order_by("name_uk"))
    posts = list(
        BlogPost.objects.filter(status=BlogPost.Status.PUBLISHED, published_at__isnull=False)
    )
    updated = max(x.updated_at for x in regions + posts) if regions or posts else None
    parts = [
        "# VyshyvankaDaily: повні тексти / full texts",
        "",
        "> Орнаменти української вишивки 27 регіонів України з джерелами, а також статті блогу. "
        "Кожен розділ - окрема сторінка сайту українською, а потім англійською. Короткий "
        f"перелік сторінок: {base}/llms.txt. Як ми працюємо з джерелами: {base}/sources/.",
    ]
    if updated:
        parts += ["", f"Оновлено / Updated: {updated:%Y-%m-%d}"]
    from apps.patterns.services.symbols import data as symbols_data
    from apps.patterns.services.symbols import page_markdown

    for lang, prefix in (("uk", ""), ("en", "/en")):
        parts += ["", f"## {symbols_data()[lang]['title']}", f"URL: {base}{prefix}/symbols/", ""]
        parts.append(page_markdown(lang))
    for r in regions:
        parts += ["", f"## {r.name_uk}", f"URL: {base}/regions/{r.slug}/", ""]
        parts.append(html_to_markdown(r.symbolism_description_uk))
        sources = [_source_line(s) for s in r.sources.all()]
        if sources:
            parts += ["", "### Джерела / Sources", *sources]
        if r.symbolism_description_en:
            parts += ["", f"## {r.name_en or r.name_uk} (English)"]
            parts += [f"URL: {base}/en/regions/{r.slug}/", ""]
            parts.append(html_to_markdown(r.symbolism_description_en))
    for post in posts:
        parts += ["", f"## {post.title_uk}", f"URL: {base}/blog/{post.slug}/"]
        parts += [_post_dates(post), ""]
        parts.append(html_to_markdown(post.body))
        if post.body_en and post.title_en:
            parts += ["", f"## {post.title_en} (English)", f"URL: {base}/en/blog/{post.slug}/", ""]
            parts.append(html_to_markdown(post.body_en))
    parts.append("")
    return HttpResponse("\n".join(parts), content_type="text/plain; charset=utf-8")


def _guess_page(path):
    """Найближча стаття чи регіон для адреси з друкарською помилкою."""
    from apps.blog.models import BlogPost
    from apps.patterns.models import Region

    parts = [p for p in path.lower().split("/") if p and p != "en"]
    if not parts:
        return None
    slug = parts[-1]
    if parts[0] == "blog":
        pages = {p.slug: p for p in BlogPost.objects.filter(status=BlogPost.Status.PUBLISHED)}
    elif parts[0] == "regions":
        pages = {r.slug: r for r in Region.objects.verified()}
    else:
        return None
    match = difflib.get_close_matches(slug, list(pages), n=1, cutoff=0.75)
    return pages[match[0]] if match else None


def page_not_found(request, exception=None):
    """404 з підказкою схожої сторінки й останніми статтями."""
    from django.db.models import F

    from apps.blog.models import BlogPost

    latest_posts = list(
        BlogPost.objects.filter(status=BlogPost.Status.PUBLISHED)
        .select_related("category")
        .order_by(F("published_at").desc(nulls_last=True), "-pk")[:3]
    )
    context = {"latest_posts": latest_posts, "suggestion": _guess_page(request.path)}
    return render(request, "404.html", context, status=404)
