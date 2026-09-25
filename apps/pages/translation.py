from modeltranslation.translator import TranslationOptions, register

from .models import FAQCategory, FAQItem, StaticPage


@register(StaticPage)
class StaticPageTranslationOptions(TranslationOptions):
    fields = ("title", "body")


@register(FAQItem)
class FAQItemTranslationOptions(TranslationOptions):
    fields = ("question", "answer")


@register(FAQCategory)
class FAQCategoryTranslationOptions(TranslationOptions):
    fields = ("name",)
