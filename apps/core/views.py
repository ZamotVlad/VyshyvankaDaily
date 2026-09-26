import re
from datetime import timedelta

from django.conf import settings
from django.http import HttpResponse, HttpResponsePermanentRedirect, HttpResponseRedirect
from django.shortcuts import render
from django.templatetags.static import static
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.utils.translation import check_for_language

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
    Закриваємо від індексації приватне й службове. Архів із фільтрами
    навмисно НЕ блокуємо тут - краще дозволити сканування й покластись
    на canonical, інакше робот не побачить сам canonical-тег на
    заблокованій сторінці.

    /pattern/ - виняток: окремі сторінки днів тонкі за вмістом і не
    потрібні в індексі (рішення власника проєкту, 27.09.2026). Уже
    мають noindex на самій сторінці (views.py, is_today == False) -
    той тег лишається активним і прибере з видачі те, що вже
    проіндексовано раніше. Disallow тут - додатково, щоб зупинити
    подальше сканування нових днів.
    """
    private = ["/accounts/", "/profile/settings/", "/collection/", "/patterns/debug/"]
    lines = [
        "User-agent: *",
        *(f"Disallow: {prefix}{path}" for path in private for prefix in ("", "/en")),
        *(f"Disallow: {prefix}/pattern/" for prefix in ("", "/en")),
        "Disallow: /admin/",
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
