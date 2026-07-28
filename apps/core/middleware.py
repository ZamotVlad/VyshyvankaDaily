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
    CSP: суворо для script-src (головний захист від XSS - шкідливий
    JS не виконається, навіть якщо десь потрапить у сторінку), дозволено
    unsafe-inline лише для style-src. Причина: частина стилів на сайті -
    кольори регіонів/мотивів із бази даних, їх неможливо винести в
    статичний CSS-клас наперед. Inline-стилі не можуть виконати код,
    тому цей виняток низькоризиковий і є свідомим постійним рішенням,
    не тимчасовим компромісом.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        response["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' https://static.cloudflareinsights.com; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com; "
            "img-src 'self' data:; "
            "connect-src 'self'; "
            "object-src 'none'; "
            "base-uri 'self'; "
            "frame-ancestors 'none';"
        )
        return response
