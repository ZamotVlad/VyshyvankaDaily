from django.contrib import admin
from django.utils.html import format_html
from modeltranslation.admin import TranslationAdmin
from unfold.admin import ModelAdmin

from .models import BlogCategory, BlogPost, GuestPostSubmission


@admin.register(BlogCategory)
class BlogCategoryAdmin(TranslationAdmin, ModelAdmin):
    list_display = ("name", "slug", "is_active", "post_count")
    list_filter = ("is_active",)
    search_fields = ("name_uk", "name_en")
    prepopulated_fields = {"slug": ("name_uk",)}

    @admin.display(description="Статей")
    def post_count(self, obj):
        return BlogPost.objects.filter(category=obj).count()


@admin.register(BlogPost)
class BlogPostAdmin(TranslationAdmin, ModelAdmin):
    list_display = ("title", "status_badge", "post_type", "category", "published_at")
    list_filter = ("status", "post_type", "category")
    search_fields = ("title_uk", "title_en")
    prepopulated_fields = {"slug": ("title_uk",)}
    filter_horizontal = ("sources",)
    readonly_fields = ("view_count",)
    autocomplete_fields = ("related_region",)
    list_per_page = 30

    fieldsets = (
        (
            "Основне",
            {
                "fields": ("title", "slug", "excerpt", "body"),
            },
        ),
        (
            "Публікація",
            {
                "fields": ("status", "post_type", "category", "published_at"),
            },
        ),
        (
            "Зв'язки",
            {
                "fields": ("related_region", "sources"),
            },
        ),
        (
            "SEO",
            {
                "fields": ("seo_title", "seo_description"),
                "classes": ("collapse",),
            },
        ),
        (
            "Службове",
            {
                "fields": ("view_count",),
                "classes": ("collapse",),
            },
        ),
    )

    @admin.display(description="Статус")
    def status_badge(self, obj):
        published = obj.status == "published"
        return format_html(
            '<span style="color: {}; font-weight: 600;">{}</span>',
            "#3A7D2C" if published else "#A69B8D",
            obj.get_status_display(),
        )


@admin.register(GuestPostSubmission)
class GuestPostSubmissionAdmin(ModelAdmin):
    # Навмисно мінімальна конфігурація: я не маю певності щодо точних
    # назв полів цієї моделі (писалась на початку Stage 4). Так вона
    # гарантовано не впаде на manage.py check. Коли скинеш мені реальні
    # поля з models.py - допишу list_display, фільтри й пошук за один раз.
    list_per_page = 30
