from django.contrib import admin, messages
from django.utils.html import format_html
from modeltranslation.admin import TranslationAdmin
from unfold.admin import ModelAdmin

from .models import DailyPattern, Motif, Region, RegionPhoto, Source
from .services.generation import CURRENT_ALGORITHM_VERSION, retry_fallback_pattern
from .services.pattern_builder import build_svg_for_date


class RegionPhotoInline(admin.TabularInline):
    model = RegionPhoto
    extra = 1
    fields = ("thumbnail_url", "image_url", "caption", "source_note", "order", "is_active")


@admin.register(Region)
class RegionAdmin(TranslationAdmin, ModelAdmin):
    list_display = (
        "name",
        "verification_badge",
        "is_active",
        "rotation_order",
        "motif_count",
        "palette_preview",
        "keyword_badge",
    )
    list_filter = ("verification_status", "is_active")
    search_fields = ("name_uk", "name_en", "slug")
    prepopulated_fields = {"slug": ("name_uk",)}
    filter_horizontal = ("sources",)
    inlines = [RegionPhotoInline]
    ordering = ("rotation_order",)
    list_per_page = 30
    actions = ["mark_verified", "mark_pending"]

    fieldsets = (
        (
            "Основне",
            {
                "fields": ("name", "slug", "is_active", "rotation_order"),
            },
        ),
        (
            "SEO",
            {
                "fields": ("target_keyword", "seo_title", "seo_description"),
                "classes": ("collapse",),
            },
        ),
        (
            "Символіка",
            {
                "fields": ("symbolism_description",),
            },
        ),
        (
            "Візуал",
            {
                "fields": ("dominant_colors", "shirt_cut_type"),
            },
        ),
        (
            "Джерела й перевірка",
            {
                "fields": ("sources", "verification_status"),
            },
        ),
    )

    @admin.display(description="Статус")
    def verification_badge(self, obj):
        verified = obj.verification_status == "verified"
        return format_html(
            '<span style="color: {}; font-weight: 600;">{}</span>',
            "#3A7D2C" if verified else "#C23B2E",
            obj.get_verification_status_display(),
        )

    @admin.display(description="Ключове слово")
    def keyword_badge(self, obj):
        if obj.target_keyword:
            return format_html(
                '<span style="color: #3A7D2C;">{}</span>',
                obj.target_keyword,
            )
        return format_html('<span style="color: #C23B2E;">—</span>')

    @admin.display(description="Мотивів")
    def motif_count(self, obj):
        return Motif.objects.filter(compatible_regions=obj).count()

    @admin.display(description="Палітра")
    def palette_preview(self, obj):
        colors = obj.dominant_colors or []
        swatches = "".join(
            f'<span style="display:inline-block;width:14px;height:14px;'
            f"border-radius:3px;border:1px solid #666;background:{c};"
            f'margin-right:3px;"></span>'
            for c in colors[:5]
        )
        return format_html(swatches) if swatches else "-"

    @admin.action(description="Позначити обрані як «Верифіковано»")
    def mark_verified(self, request, queryset):
        updated = queryset.update(verification_status="verified")
        self.message_user(request, f"Оновлено регіонів: {updated}")

    @admin.action(description="Позначити обрані як «На перевірці»")
    def mark_pending(self, request, queryset):
        updated = queryset.update(verification_status="pending")
        self.message_user(request, f"Оновлено регіонів: {updated}")


@admin.register(Motif)
class MotifAdmin(TranslationAdmin, ModelAdmin):
    list_display = ("name", "verification_badge", "region_list")
    list_filter = ("verification_status",)
    search_fields = ("name_uk", "name_en")
    filter_horizontal = ("compatible_regions", "sources")
    list_per_page = 30

    fieldsets = (
        (
            "Основне",
            {
                "fields": ("name", "verification_status"),
            },
        ),
        (
            "Значення",
            {
                "fields": ("meaning_description",),
            },
        ),
        (
            "Геометрія (pixel_grid_v1)",
            {
                "fields": ("geometry_parameters",),
                "description": (
                    "JSON із ключами grid і palette. Редагувати обережно: "
                    "неправильний формат зламає рендер орнаменту."
                ),
            },
        ),
        (
            "Зв'язки",
            {
                "fields": ("compatible_regions", "sources"),
            },
        ),
    )

    @admin.display(description="Статус")
    def verification_badge(self, obj):
        verified = obj.verification_status == "verified"
        return format_html(
            '<span style="color: {}; font-weight: 600;">{}</span>',
            "#3A7D2C" if verified else "#C23B2E",
            obj.get_verification_status_display(),
        )

    @admin.display(description="Регіони")
    def region_list(self, obj):
        names = [r.name for r in obj.compatible_regions.all()[:3]]
        return ", ".join(names) if names else "-"


@admin.register(Source)
class SourceAdmin(ModelAdmin):
    list_display = ("name", "source_type", "author_or_institution", "publication_year")
    list_filter = ("source_type",)
    search_fields = ("name", "author_or_institution")
    list_per_page = 30


@admin.register(DailyPattern)
class DailyPatternAdmin(ModelAdmin):
    list_display = ("date", "region", "generation_status", "algorithm_version", "view_count")
    list_filter = ("generation_status", "region", "algorithm_version")
    actions = ["retry_fallbacks"]
    date_hierarchy = "date"
    search_fields = ("region__name_uk",)
    readonly_fields = ("seed", "svg_content", "view_count")
    autocomplete_fields = ("region",)
    list_per_page = 50

    @admin.action(description="Перегенерувати дні з резервним орнаментом")
    def retry_fallbacks(self, request, queryset):
        fixed = 0
        for pattern in queryset.filter(generation_status=DailyPattern.GenerationStatus.FALLBACK):
            try:
                retry_fallback_pattern(pattern, CURRENT_ALGORITHM_VERSION, build_svg_for_date)
                fixed += 1
            except Exception as exc:
                self.message_user(request, f"{pattern.date}: {exc}", messages.ERROR)
        self.message_user(request, f"Перегенеровано: {fixed}")
