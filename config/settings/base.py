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
    # modeltranslation має бути ДО django.contrib.admin
    "modeltranslation",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Кастомні застосунки проєкту
    "apps.core",
    "apps.accounts",
    "apps.patterns",
    "apps.blog",
    "apps.pages",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",  # Обов'язково для i18n
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
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
