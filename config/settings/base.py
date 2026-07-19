from pathlib import Path

import environ
from django.utils.translation import gettext_lazy as _

# Шлях до кореня проєкту: config/settings/base.py -> 3 рівні вгору
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Ініціалізація environ
env = environ.Env(DEBUG=(bool, False), ALLOWED_HOSTS=(list, []))

# Читання .env файлу (якщо він існує, наприклад для локальної розробки)
environ.Env.read_env(BASE_DIR / ".env")

# Секретний ключ і режим дебагу тепер читаються зі змінних середовища
SECRET_KEY = env("SECRET_KEY")
DEBUG = env("DEBUG")
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS")

INSTALLED_APPS = [
    "unfold",
    "modeltranslation",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sites",
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "allauth.socialaccount.providers.google",
    "anymail",
    # Кастомні застосунки проєкту
    "apps.core",
    "apps.accounts",
    "apps.patterns",
    "apps.blog",
    "apps.pages",
    "django_ckeditor_5",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",  # Обов'язково для i18n
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "allauth.account.middleware.AccountMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],  # Задаємо шлях до глобальних шаблонів
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# База даних: SQLite на старті (відповідно до ADR 2)
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

# Мультимовність
LANGUAGE_CODE = "uk"  # Українська як основна

LANGUAGES = [
    ("uk", _("Ukrainian")),
    ("en", _("English")),
]

# Налаштування django-modeltranslation
MODELTRANSLATION_DEFAULT_LANGUAGE = "uk"
MODELTRANSLATION_LANGUAGES = ("uk", "en")

LOCALE_PATHS = [
    BASE_DIR / "locale",
]

TIME_ZONE = "Europe/Kyiv"

USE_I18N = True
USE_TZ = True

# Статичні файли
STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


SITE_ID = 1

AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
]

# Автентифікація через пошту (розділ 7.1 ТЗ)
ACCOUNT_LOGIN_METHODS = {"email"}
ACCOUNT_SIGNUP_FIELDS = ["email*", "password1*", "password2*"]
ACCOUNT_EMAIL_VERIFICATION = "mandatory"

ANYMAIL = {
    "POSTMARK_SERVER_TOKEN": env("POSTMARK_SERVER_TOKEN", default=""),
}
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", default="noreply@vyshyvankadaily.local")


LOGIN_REDIRECT_URL = "patterns:home"


SOCIALACCOUNT_PROVIDERS = {
    "google": {
        "APP": {
            "client_id": env("GOOGLE_CLIENT_ID", default=""),
            "secret": env("GOOGLE_CLIENT_SECRET", default=""),
            "key": "",
        },
        "SCOPE": ["profile", "email"],
        "AUTH_PARAMS": {"access_type": "online"},
    }
}


UNFOLD = {
    "DASHBOARD_CALLBACK": "apps.core.dashboard.dashboard_callback",
    "SITE_TITLE": "VyshyvankaDaily",
    "SITE_HEADER": "VyshyvankaDaily",
    "COLORS": {
        # Палітра на основі кольорів вишивки: червоний і чорний як акценти
        # на нейтральному тлі (розділ 14.1 ТЗ).
        "primary": {
            "50": "254 242 242",
            "100": "254 226 226",
            "200": "254 202 202",
            "300": "252 165 165",
            "400": "248 113 113",
            "500": "220 38 38",
            "600": "185 28 28",
            "700": "153 27 27",
            "800": "127 29 29",
            "900": "69 10 10",
        },
    },
    "SIDEBAR": {
        "show_search": True,
        "navigation": [
            {
                "title": "Контент дня",
                "items": [
                    {"title": "Щоденні патерни", "link": "/admin/patterns/dailypattern/"},
                ],
            },
            {
                "title": "Довідники",
                "items": [
                    {"title": "Регіони", "link": "/admin/patterns/region/"},
                    {"title": "Мотиви", "link": "/admin/patterns/motif/"},
                    {"title": "Джерела", "link": "/admin/patterns/source/"},
                ],
            },
            {
                "title": "Блог",
                "items": [
                    {"title": "Статті", "link": "/admin/blog/blogpost/"},
                    {"title": "Категорії статей", "link": "/admin/blog/blogcategory/"},
                    {
                        "title": "Заявки на гостьові пости",
                        "link": "/admin/blog/guestpostsubmission/",
                    },
                ],
            },
            {
                "title": "Спільнота",
                "items": [
                    {"title": "Користувачі", "link": "/admin/auth/user/"},
                    {"title": "Профілі", "link": "/admin/accounts/profile/"},
                    {"title": "Збережені патерни", "link": "/admin/patterns/savedpattern/"},
                ],
            },
            {
                "title": "Звернення",
                "items": [
                    {"title": "Контактні повідомлення", "link": "/admin/pages/contactmessage/"},
                ],
            },
            {
                "title": "Сторінки",
                "items": [
                    {"title": "Статичні сторінки", "link": "/admin/pages/staticpage/"},
                    {"title": "Категорії FAQ", "link": "/admin/pages/faqcategory/"},
                    {"title": "Пункти FAQ", "link": "/admin/pages/faqitem/"},
                ],
            },
        ],
    },
}


CKEDITOR_5_CONFIGS = {
    "default": {
        "toolbar": [
            "heading",
            "|",
            "bold",
            "italic",
            "|",
            "link",
            "|",
            "bulletedList",
            "numberedList",
            "|",
            "blockQuote",
            "|",
            "insertTable",
            "|",
            "codeBlock",
            "|",
            "sourceEditing",
        ],
    },
}
CKEDITOR_5_UPLOAD_FILE_TYPES = ["jpeg", "jpg", "png"]
CKEDITOR_5_MAX_FILE_SIZE = 5  # МБ (розділ 14.5 ТЗ — обмеження за розміром)

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# Дозволений перелік HTML-тегів/атрибутів для санітизації тіла статті
# (розділ 14.5 ТЗ) — навмисно обмежений, не весь HTML5.
ALLOWED_BLOG_HTML_TAGS = [
    "p",
    "br",
    "strong",
    "em",
    "a",
    "ul",
    "ol",
    "li",
    "blockquote",
    "h2",
    "h3",
    "h4",
    "table",
    "thead",
    "tbody",
    "tr",
    "th",
    "td",
    "code",
    "pre",
]
ALLOWED_BLOG_HTML_ATTRIBUTES = {
    "a": ["href", "title"],
}
