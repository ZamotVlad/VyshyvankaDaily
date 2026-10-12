"""IndexNow: повідомляє Bing (і через нього ChatGPT, Copilot) про нові й змінені сторінки."""

import json
import logging
import urllib.request

from django.conf import settings
from django.urls import reverse
from django.utils import translation

logger = logging.getLogger(__name__)

ENDPOINT = "https://api.indexnow.org/indexnow"
DEFAULT_HOST = "vyshyvankadaily.live"


def host():
    return settings.CANONICAL_HOST or DEFAULT_HOST


def bilingual_urls(viewname, *args):
    """Абсолютні адреси сторінки українською й англійською."""
    urls = []
    for lang in ("uk", "en"):
        with translation.override(lang):
            urls.append(f"https://{host()}{reverse(viewname, args=args)}")
    return urls


def submit(urls):
    """Надсилає адреси; повертає HTTP-статус або None, якщо ключа немає чи запит упав."""
    key = settings.INDEXNOW_KEY
    urls = list(dict.fromkeys(urls))
    if not key or not urls:
        return None
    payload = {
        "host": host(),
        "key": key,
        "keyLocation": f"https://{host()}/{key}.txt",
        "urlList": urls[:10000],
    }
    request = urllib.request.Request(
        ENDPOINT,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            return response.status
    except Exception:
        logger.exception("IndexNow: не вдалося надіслати %s адрес", len(urls))
        return None
