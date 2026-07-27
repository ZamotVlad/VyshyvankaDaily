from django.contrib import admin
from django.utils.html import format_html
from modeltranslation.admin import TranslationAdmin
from unfold.admin import ModelAdmin

from .models import DailyPattern, Motif, Region, Source


@admin.register(Region)
class RegionAdmin(TranslationAdmin, ModelAdmin):
    list_display = (
        "name",
        "verification_badge",
        "is_active",
        "rotation_order",
        "motif_count",
        "palette_preview",
    )
    list_filter = ("verification_status", "is_active")
    search_fields = ("name_uk", "name_en", "slug")
    prepopulated_fields = {"slug": ("name_uk",)}
    filter_horizontal = ("sources",)
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
    # УВАГА: якщо в чинному файлі вже є дія force_regenerate_pattern
    # (Stage 4, ADR 33) - перенеси її сюди з робочого коду. Я навмисно
    # її не переписую, бо не пам'ятаю точну сигнатуру generate_daily_pattern
    # і не хочу зламати те, що вже працює.
    list_display = ("date", "region", "algorithm_version", "view_count")
    list_filter = ("region", "algorithm_version")
    date_hierarchy = "date"
    search_fields = ("region__name_uk",)
    readonly_fields = ("seed", "svg_content", "view_count")
    autocomplete_fields = ("region",)
    list_per_page = 50
