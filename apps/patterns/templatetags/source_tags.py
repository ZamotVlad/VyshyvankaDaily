import re

from django import template

register = template.Library()

# Джерела показуємо лише текстом: без адрес сайтів і службових підписів перед ними.
LABELS = re.compile(r"\s*(Повний текст|Режим доступу|Доступно)\s*:\s*")
URL = re.compile(
    r"(?:https?://)?(?:www\.)?[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}(?:/\S*)?"
)


@register.filter
def source_reference(value):
    text = URL.sub("", LABELS.sub(" ", value or ""))
    text = re.sub(r"\s+([.,;])", r"\1", text)
    text = re.sub(r"^[\s.,;]+|[\s,;]+$", "", re.sub(r"\s{2,}", " ", text))
    return "" if not re.search(r"\w", text) else text
