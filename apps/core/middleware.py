import re
from urllib.parse import urlsplit

from django.conf import settings
from django.http import HttpResponsePermanentRedirect


class CanonicalHostMiddleware:
    """301 на основний домен: www.<домен> та *.herokuapp.com (якщо задано CANONICAL_HOST)."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        host = request.META.get("HTTP_HOST", "").split(":")[0].lower()
        target = None
        if host.startswith("www.") and host[4:] in settings.ALLOWED_HOSTS:
            target = host[4:]
        elif settings.CANONICAL_HOST and host.endswith(".herokuapp.com"):
            target = settings.CANONICAL_HOST
        if target:
            scheme = "https" if settings.SECURE_SSL_REDIRECT else request.scheme
            return HttpResponsePermanentRedirect(f"{scheme}://{target}{request.get_full_path()}")
        # /a//b -> /a/b: інакше адреса з подвійною косою віддає 404
        if "//" in request.path:
            path = re.sub(r"/{2,}", "/", request.path)
            query = request.META.get("QUERY_STRING")
            return HttpResponsePermanentRedirect(f"{path}?{query}" if query else path)
        return self.get_response(request)


class HideServerHeaderMiddleware:
    """
    Прибирає деталізацію версії із заголовка Server (ZAP/StackHawk:
    'Server Leaks Version Information'). Сам dev-сервер Django завжди
    підставляє власну версію - тут просто затираємо її на виході.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if "Server" in response:
            response["Server"] = "server"
        return response


# Umami Cloud шле події не на домен скрипта, а на окремі шлюзи.
UMAMI_CLOUD_GATEWAYS = ("https://gateway.umami.is", "https://api-gateway.umami.dev")


def _analytics_origins():
    """Домени Umami для CSP (скрипт, відправка подій) - лише коли статистику увімкнено."""
    if not settings.UMAMI_WEBSITE_ID:
        return "", ""
    parts = urlsplit(settings.UMAMI_SCRIPT_URL)
    script = f" {parts.scheme}://{parts.netloc}"
    connect = script
    if parts.netloc == "cloud.umami.is":
        connect += "".join(f" {o}" for o in UMAMI_CLOUD_GATEWAYS)
    return script, connect


class ContentSecurityPolicyMiddleware:
    """
    CSP: суворий для публічного сайту (script-src без unsafe-inline/
    unsafe-eval - головний захист від XSS). Для адмінки (/vd/...) -
    послаблений script-src, бо Unfold/Alpine.js вимагають unsafe-eval
    для роботи. Адмінка - єдиний користувач (власник), не публічний
    відвідувач, тому цей компроміс обмежений лише нею, не всім сайтом.
    """

    ADMIN_PREFIX = "/vd/"

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        is_admin = request.path.startswith(self.ADMIN_PREFIX)
        analytics, analytics_connect = ("", "") if is_admin else _analytics_origins()
        script_src = (
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            if is_admin
            else f"script-src 'self'{analytics}; "
        )

        fonts = "style-src 'self' 'unsafe-inline'; font-src 'self'; "

        response["Content-Security-Policy"] = (
            "default-src 'self'; " + script_src + fonts + "img-src 'self' data:; "
            f"connect-src 'self'{analytics_connect}; "
            "object-src 'none'; "
            "base-uri 'self'; "
            "frame-ancestors 'none';"
        )

        response["Permissions-Policy"] = (
            "camera=(), microphone=(), geolocation=(), payment=(), usb=(), interest-cohort=()"
        )
        return response
