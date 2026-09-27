from django import template
from django.utils.html import urlize
from django.utils.safestring import mark_safe
from django.utils.translation import gettext

register = template.Library()

# Службові підписи всередині Source.reference - перекладаються, бібліографія ні.
LABELS = ("Повний текст:", "Режим доступу:", "Доступно:")


@register.filter
def source_reference(value):
    text = value or ""
    for label in LABELS:
        text = text.replace(label, gettext(label))
    # urlize з autoescape екранує весь текст, тож результат безпечний
    return mark_safe(urlize(text, nofollow=True, autoescape=True))
