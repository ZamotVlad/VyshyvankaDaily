from django.contrib import admin
from django.db.models import Count
from django.utils.html import format_html
from modeltranslation.admin import TranslationAdmin
from unfold.admin import ModelAdmin

from .models import Author, BlogCategory, BlogPost, GuestPostSubmission


@admin.register(Author)
class AuthorAdmin(TranslationAdmin, ModelAdmin):
    list_display = ("name", "slug", "post_count")
    search_fields = ("name_uk", "name_en")
    prepopulated_fields = {"slug": ("name_uk",)}

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(_posts=Count("posts"))

    @admin.display(description="Статей", ordering="_posts")
    def post_count(self, obj):
        return obj._posts


@admin.register(BlogCategory)
class BlogCategoryAdmin(TranslationAdmin, ModelAdmin):
    list_display = ("name", "slug", "is_active", "post_count")
    list_filter = ("is_active",)
    search_fields = ("name_uk", "name_en")
    prepopulated_fields = {"slug": ("name_uk",)}

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(_posts=Count("posts"))

    @admin.display(description="Статей", ordering="_posts")
    def post_count(self, obj):
        return obj._posts


@admin.register(BlogPost)
class BlogPostAdmin(TranslationAdmin, ModelAdmin):
    list_display = (
        "title",
        "status_badge",
        "post_type",
        "category",
        "published_at",
        "keyword_badge",
    )
    list_filter = ("status", "post_type", "category")
    list_select_related = ("category",)
    date_hierarchy = "published_at"
    search_fields = ("title_uk", "title_en", "slug", "target_keyword")
    prepopulated_fields = {"slug": ("title_uk",)}
    filter_horizontal = ("sources",)
    autocomplete_fields = ("related_region",)
    list_per_page = 30

    fieldsets = (
        (
            "Основне",
            {
                "fields": (
                    "title",
                    "slug",
                    "excerpt",
                    "body",
                    "body_en",
                    "cover_image_url",
                    "cover_image_alt",
                ),
            },
        ),
        (
            "Публікація",
            {
                "fields": (
                    "status",
                    "post_type",
                    "category",
                    "published_at",
                    "blog_author",
                    "guest_author_name",
                    "submitter_contact",
                ),
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
                "fields": ("seo_title", "seo_description", "target_keyword"),
            },
        ),
    )

    class Media:
        js = ("js/admin_seo_counter.js",)

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        field = super().formfield_for_dbfield(db_field, request, **kwargs)
        if db_field.name.startswith(("excerpt", "seo_description")):
            field.widget.attrs["rows"] = 3
        return field

    @admin.display(description="Статус")
    def status_badge(self, obj):
        published = obj.status == "published"
        return format_html(
            '<span style="color: {}; font-weight: 600;">{}</span>',
            "#3A7D2C" if published else "#A69B8D",
            obj.get_status_display(),
        )

    @admin.display(description="Ключове слово")
    def keyword_badge(self, obj):
        if obj.target_keyword:
            return format_html(
                '<span style="color: #3A7D2C;">{}</span>',
                obj.target_keyword,
            )
        return format_html('<span style="color: #C23B2E;">{}</span>', "-")


@admin.register(GuestPostSubmission)
class GuestPostSubmissionAdmin(ModelAdmin):
    list_display = ("proposed_topic", "contact_name", "email", "review_status", "created_at")
    list_filter = ("review_status", "created_at")
    list_editable = ("review_status",)
    search_fields = ("proposed_topic", "contact_name", "email", "brand_name")
    readonly_fields = (
        "contact_name",
        "email",
        "brand_name",
        "proposed_topic",
        "proposal_description",
        "submitter_ip",
        "created_at",
    )
    fields = ("review_status", *readonly_fields)
    date_hierarchy = "created_at"
    list_per_page = 30

    actions = ["mark_rejected", "mark_in_review"]

    def has_add_permission(self, request):
        return False

    @admin.action(description="Позначити як «Відхилено»")
    def mark_rejected(self, request, queryset):
        updated = queryset.update(review_status=GuestPostSubmission.ReviewStatus.REJECTED)
        self.message_user(request, f"Відхилено заявок: {updated}")

    @admin.action(description="Позначити як «На розгляді»")
    def mark_in_review(self, request, queryset):
        updated = queryset.update(review_status=GuestPostSubmission.ReviewStatus.IN_REVIEW)
        self.message_user(request, f"Оновлено заявок: {updated}")
