from modeltranslation.translator import TranslationOptions, register

from .models import BlogCategory, BlogPost


@register(BlogCategory)
class BlogCategoryTranslationOptions(TranslationOptions):
    fields = ("name", "description")


@register(BlogPost)
class BlogPostTranslationOptions(TranslationOptions):
    # "body" НЕ перекладне — CKEditor5Field не підтримується
    # django-modeltranslation (відоме, задокументоване обмеження бібліотеки,
    # issue #576 у репозиторії modeltranslation). Тіло статті спільне для
    # обох мов; перекладними лишаються тільки текстові поля.
    fields = ("title", "excerpt", "seo_title", "seo_description")
