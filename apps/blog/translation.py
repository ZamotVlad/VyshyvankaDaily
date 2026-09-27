from modeltranslation.translator import TranslationOptions, register

from .models import Author, BlogCategory, BlogPost


@register(BlogCategory)
class BlogCategoryTranslationOptions(TranslationOptions):
    fields = ("name", "description")


@register(BlogPost)
class BlogPostTranslationOptions(TranslationOptions):
    # "body" НЕ перекладне — CKEditor5Field не підтримується
    # django-modeltranslation (відоме, задокументоване обмеження бібліотеки,
    # issue #576 у репозиторії modeltranslation). Тіло статті спільне для
    # обох мов; перекладними лишаються тільки текстові поля.
    fields = (
        "title",
        "excerpt",
        "cover_image_alt",
        "seo_title",
        "seo_description",
        "target_keyword",
    )


@register(Author)
class AuthorTranslationOptions(TranslationOptions):
    fields = ("name", "bio")
