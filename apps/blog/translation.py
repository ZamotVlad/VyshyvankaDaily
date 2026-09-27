from modeltranslation.translator import TranslationOptions, register

from .models import Author, BlogCategory, BlogPost


@register(BlogCategory)
class BlogCategoryTranslationOptions(TranslationOptions):
    fields = ("name", "description")


@register(BlogPost)
class BlogPostTranslationOptions(TranslationOptions):
    # body не реєструється: CKEditor5Field не підтримується modeltranslation
    # (issue #576). Англійський текст - окреме поле BlogPost.body_en.
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
