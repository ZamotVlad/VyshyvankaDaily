from modeltranslation.translator import TranslationOptions, register

from .models import FAQItem, StaticPage


@register(StaticPage)
class StaticPageTranslationOptions(TranslationOptions):
    fields = ("title", "body")


@register(FAQItem)
class FAQItemTranslationOptions(TranslationOptions):
    fields = ("question", "answer")
