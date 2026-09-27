from django import template
from django.utils.html import urlize
from django.utils.translation import gettext

register = template.Library()

# Службові підписи всередині Source.reference - перекладаються, бібліографія ні.
LABELS = ("Повний текст:", "Режим доступу:", "Доступно:")


@register.filter
def source_reference(value):
    text = value or ""
    for label in LABELS:
        text = text.replace(label, gettext(label))
    return urlize(text, nofollow=True, autoescape=True)
