"""Вбудований у сторінку CSS: без окремих запитів, що блокують перший показ."""

import re
from functools import cache

from django import template
from django.conf import settings
from django.contrib.staticfiles import finders
from django.utils.safestring import mark_safe

register = template.Library()


def _minify(css):
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    css = re.sub(r"\s+", " ", css)
    return re.sub(r"\s*([{};])\s*", r"\1", css).strip()


def _read(paths):
    return "".join(_minify(open(finders.find(p), encoding="utf-8").read()) for p in paths)


_cached = cache(_read)


@register.simple_tag
def inline_css(*paths):
    css = _read(paths) if settings.DEBUG else _cached(paths)
    return mark_safe(f"<style>{css}</style>")


_LOCAL_STATIC = re.compile(
    r"^(?:https?://(?:www\.)?vyshyvankadaily\.live)?/static/(?P<path>[^?#\"]+)$"
)
_SRC = re.compile(r'(src|data-full)="([^"]+)"')


@cache
def _variant(path, size):
    stem, dot, ext = path.rpartition(".")
    candidate = f"{stem}-{size}.{ext}"
    return candidate if dot and finders.find(candidate) else path


def local_static(url, size=""):
    """Адреса нашого статичного файлу -> хешована: браузер кешує її на рік.
    size - зменшена копія поруч (photo-64.webp), якщо вона є."""
    match = _LOCAL_STATIC.match(url or "")
    if not match:
        return url
    from django.templatetags.static import static

    path = _variant(match["path"], size) if size else match["path"]
    try:
        return static(path)
    except ValueError:
        return url


@register.filter
def asset(url, size=""):
    return local_static(url, str(size))


def hash_static_srcs(html):
    return _SRC.sub(lambda m: f'{m[1]}="{local_static(m[2])}"', html or "")
