from django.contrib import admin
from django_ckeditor_5.widgets import CKEditor5Widget
from modeltranslation.admin import TranslationAdmin
from unfold.admin import ModelAdmin

from .models import BlogCategory, BlogPost, GuestPostSubmission


@admin.register(BlogCategory)
class BlogCategoryAdmin(TranslationAdmin, ModelAdmin):
    list_display = ("name", "is_active")
    list_filter = ("is_active",)


@admin.register(BlogPost)
class BlogPostAdmin(TranslationAdmin, ModelAdmin):
    list_display = ("title", "status", "post_type", "category", "published_at", "view_count")
    list_filter = ("status", "post_type", "category")
    search_fields = ("title",)
    filter_horizontal = ("sources",)
    prepopulated_fields = {"slug": ("title",)}

    formfield_overrides = {
        BlogPost._meta.get_field("body").__class__: {
            "widget": CKEditor5Widget(config_name="default")
        },
    }


@admin.register(GuestPostSubmission)
class GuestPostSubmissionAdmin(ModelAdmin):
    list_display = ("contact_name", "proposed_topic", "review_status", "created_at")
    list_filter = ("review_status",)
    readonly_fields = (
        "contact_name",
        "email",
        "brand_name",
        "proposed_topic",
        "proposal_description",
        "submitter_ip",
    )
    actions = ["mark_reviewed"]

    @admin.action(description="Позначити розглянутими")
    def mark_reviewed(self, request, queryset):
        queryset.update(review_status=GuestPostSubmission.ReviewStatus.APPROVED)
