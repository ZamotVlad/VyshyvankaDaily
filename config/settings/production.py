from .base import *  # noqa

DEBUG = False

EMAIL_BACKEND = "anymail.backends.postmark.EmailBackend"

# Стиснення + унікальні імена файлів з хешем вмісту (кешування назавжди).
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
}

# ---------- Безпека (Stage 6/7) ----------
# Перевіряти командою: python manage.py check --deploy

SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"
SECURE_REFERRER_POLICY = "same-origin"

# УВАГА, увімкнути лише ПІСЛЯ того, як HTTPS реально працює.
# PythonAnywhere і Cloudflare термінують SSL у себе, тому без
# SECURE_PROXY_SSL_HEADER цей редирект дасть нескінченний цикл.
# SECURE_SSL_REDIRECT = True
# SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# HSTS: починати з малого значення (1 година), і лише переконавшись,
# що все працює по HTTPS, підіймати до року. Помилка тут коштує дорого:
# браузери запам'ятовують заголовок і відмовляються ходити по HTTP
# рівно стільки, скільки вказано, навіть якщо ти вже все відкотив.
SECURE_HSTS_SECONDS = 3600
SECURE_HSTS_INCLUDE_SUBDOMAINS = False
SECURE_HSTS_PRELOAD = False
