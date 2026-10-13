from django.contrib import admin, messages
from django.db.models import Count
from django.urls import reverse
from django.utils.html import format_html, format_html_join
from modeltranslation.admin import TranslationAdmin
from unfold.admin import ModelAdmin, TabularInline

from .models import DailyPattern, Motif, Region, RegionPhoto, SavedPattern, Source
from .services.generation import CURRENT_ALGORITHM_VERSION, retry_fallback_pattern
from .services.pattern_builder import build_svg_for_date


class RegionPhotoInline(TabularInline):
    model = RegionPhoto
    extra = 0
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

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(_motif_count=Count("compatible_motifs"))

    class Media:
        js = ("js/admin_seo_counter.js",)

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
                "fields": (
                    "dominant_colors",
                    "generator_only_colors",
                    "accent_colors",
                    "shirt_cut_type",
                ),
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
        return format_html('<span style="color: #C23B2E;">{}</span>', "-")

    @admin.display(description="Мотивів", ordering="_motif_count")
    def motif_count(self, obj):
        return obj._motif_count

    @admin.display(description="Палітра")
    def palette_preview(self, obj):
        colors = obj.dominant_colors or []
        if not colors:
            return "-"
        return format_html_join(
            "",
            '<span style="display:inline-block;width:14px;height:14px;border-radius:3px;'
            'border:1px solid #666;background:{};margin-right:3px;"></span>',
            ((c,) for c in colors[:5]),
        )

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
    list_display = ("name", "verification_badge", "is_active", "region_list")
    list_filter = ("verification_status", "is_active", "compatible_regions")
    search_fields = ("name_uk", "name_en")
    filter_horizontal = ("compatible_regions", "sources")
    list_per_page = 30

    fieldsets = (
        (
            "Основне",
            {
                "fields": ("name", "verification_status", "is_active"),
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
                "description": "Редагувати обережно: неправильний формат зламає рендер орнаменту.",
                "classes": ("collapse",),
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

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related("compatible_regions")

    @admin.display(description="Регіони")
    def region_list(self, obj):
        names = [r.name for r in obj.compatible_regions.all()]
        if len(names) > 3:
            return f"{', '.join(names[:3])} +{len(names) - 3}"
        return ", ".join(names) if names else "-"


@admin.register(Source)
class SourceAdmin(ModelAdmin):
    list_display = ("name", "source_type", "author_or_institution", "publication_year", "usage")
    list_filter = ("source_type",)
    search_fields = ("name", "author_or_institution", "reference")
    list_per_page = 30

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .annotate(
                _regions=Count("region", distinct=True), _posts=Count("blog_posts", distinct=True)
            )
        )

    @admin.display(description="Використано")
    def usage(self, obj):
        parts = []
        if obj._regions:
            parts.append(f"регіонів: {obj._regions}")
        if obj._posts:
            parts.append(f"статей: {obj._posts}")
        return ", ".join(parts) or "-"


@admin.register(DailyPattern)
class DailyPatternAdmin(ModelAdmin):
    list_display = ("date", "region", "generation_status", "algorithm_version")
    list_filter = ("generation_status", "region", "algorithm_version")
    actions = ["retry_fallbacks"]
    date_hierarchy = "date"
    search_fields = ("region__name_uk",)
    list_select_related = ("region",)
    fields = (
        "preview",
        "date",
        "region",
        "generation_status",
        "algorithm_version",
        "seed",
        "motifs_used",
    )
    readonly_fields = fields
    list_per_page = 50

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    @admin.display(description="Орнамент")
    def preview(self, obj):
        url = reverse("patterns:pattern_detail", args=[obj.date.isoformat()])
        svg = reverse("patterns:pattern_svg", args=[obj.date.isoformat()])
        svg += f"?v={int(obj.updated_at.timestamp())}"
        return format_html(
            '<a href="{}" target="_blank" rel="noopener">'
            '<img src="{}" alt="" width="254" height="300" class="vd-pattern-preview"></a>',
            url,
            svg,
        )

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


@admin.register(SavedPattern)
class SavedPatternAdmin(ModelAdmin):
    list_display = ("pattern", "user", "created_at")
    list_filter = ("pattern__region",)
    search_fields = ("user__username", "user__email")
    list_select_related = ("pattern__region", "user")
    readonly_fields = ("pattern", "user", "created_at")
    date_hierarchy = "created_at"
    list_per_page = 50

    def has_add_permission(self, request):
        return False
