from pathlib import Path

import environ
from django.templatetags.static import static
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

CSRF_FAILURE_VIEW = "apps.core.views.csrf_failure"
LANGUAGE_COOKIE_SAMESITE = "Lax"
SECURE_CONTENT_TYPE_NOSNIFF = True

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
    "django.contrib.sitemaps",
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
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",  # Обов'язково для i18n
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "allauth.account.middleware.AccountMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "apps.core.middleware.HideServerHeaderMiddleware",
    "apps.core.middleware.ContentSecurityPolicyMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],  # Задаємо шлях до глобальних шаблонів
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.i18n",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "apps.core.context_processors.seo",
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
    "SITE_TITLE": "VyshyvankaDaily - адміністрування",
    "SITE_HEADER": "VyshyvankaDaily",
    "SITE_ICON": lambda request: static("logo/admin_icon.svg"),
    "SITE_LOGO": lambda request: static("logo/admin_icon.svg"),
    "DASHBOARD_CALLBACK": "apps.core.dashboard.dashboard_callback",
    "STYLES": [
        lambda request: static("css/admin_theme.css"),
    ],
    "COLORS": {
        "base": {
            "50": "oklch(97% 0.006 70)",
            "100": "oklch(93% 0.010 70)",
            "200": "oklch(87% 0.014 68)",
            "300": "oklch(80% 0.018 66)",
            "400": "oklch(74% 0.020 64)",
            "500": "oklch(68% 0.022 62)",
            "600": "oklch(50% 0.020 60)",
            "700": "oklch(38% 0.018 58)",
            "800": "oklch(28% 0.016 56)",
            "900": "oklch(20% 0.014 54)",
            "950": "oklch(15% 0.012 52)",
        },
        "primary": {
            "50": "oklch(96% 0.020 30)",
            "100": "oklch(91% 0.040 30)",
            "200": "oklch(83% 0.080 30)",
            "300": "oklch(74% 0.120 30)",
            "400": "oklch(64% 0.160 30)",
            "500": "oklch(56% 0.180 30)",
            "600": "oklch(48% 0.170 30)",
            "700": "oklch(41% 0.150 30)",
            "800": "oklch(34% 0.120 30)",
            "900": "oklch(28% 0.095 30)",
            "950": "oklch(20% 0.070 30)",
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
