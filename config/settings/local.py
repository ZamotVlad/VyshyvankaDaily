from .base import *  # noqa

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# WhiteNoise бере файли напряму з static/, без collectstatic - зручно для
# локальної перевірки з DEBUG=False (інакше довелось би збирати щоразу).
WHITENOISE_USE_FINDERS = True
WHITENOISE_AUTOREFRESH = True
ALLOWED_HOSTS = ["localhost", "127.0.0.1", "host.docker.internal"]
