from .base import *  # noqa

DEBUG = False

EMAIL_BACKEND = "anymail.backends.postmark.EmailBackend"

# Стиснення + унікальні імена файлів з хешем вмісту (кешування назавжди).
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
}
