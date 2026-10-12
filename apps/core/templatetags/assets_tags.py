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
