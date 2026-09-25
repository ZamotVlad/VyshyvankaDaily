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
        script_src = (
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://static.cloudflareinsights.com;"
            if is_admin
            else "script-src 'self' https://static.cloudflareinsights.com; "
        )

        response["Content-Security-Policy"] = (
            "default-src 'self'; "
            + script_src
            + "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com; "
            "img-src 'self' data:; "
            "connect-src 'self'; "
            "object-src 'none'; "
            "base-uri 'self'; "
            "frame-ancestors 'none';"
        )

        response["Permissions-Policy"] = (
            "camera=(), microphone=(), geolocation=(), payment=(), usb=(), interest-cohort=()"
        )
        return response
