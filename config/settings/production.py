import dj_database_url

from .base import *  # noqa
from .base import env

DEBUG = False

EMAIL_BACKEND = "anymail.backends.brevo.EmailBackend"

# Heroku Postgres: DATABASE_URL приходить готовим від аддону.
DATABASES = {
    "default": dj_database_url.parse(env("DATABASE_URL"), conn_max_age=600),
}

# Спільний між процесами кеш (ліміти запитів). Таблиця: createcachetable у Procfile.
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.db.DatabaseCache",
        "LOCATION": "django_cache",
    }
}

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

# Heroku router термінує TLS і проксує до dyno по HTTP, підставляючи
# X-Forwarded-Proto. Без SECURE_PROXY_SSL_HEADER request.is_secure()
# завжди поверне False, і сам SECURE_SSL_REDIRECT дасть нескінченний
# цикл редиректів (на відміну від PythonAnywhere/Cloudflare, під які
# цей коментар був написаний раніше).
# УВАГА, увімкнути SECURE_SSL_REDIRECT лише ПІСЛЯ підтвердження, що
# домен реально відповідає по HTTPS (крок 6 плану деплою).
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = True

# HSTS: починати з малого значення (1 година), і лише переконавшись,
# що все працює по HTTPS, підіймати до року. Помилка тут коштує дорого:
# браузери запам'ятовують заголовок і відмовляються ходити по HTTP
# рівно стільки, скільки вказано, навіть якщо ти вже все відкотив.
SECURE_HSTS_SECONDS = 31536000  # 1 рік
SECURE_HSTS_INCLUDE_SUBDOMAINS = False
SECURE_HSTS_PRELOAD = False
