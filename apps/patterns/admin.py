from django.contrib import admin, messages
from django.db.models import Count
from modeltranslation.admin import TranslationAdmin
from unfold.admin import ModelAdmin

from apps.patterns.services.generation import CURRENT_ALGORITHM_VERSION, force_regenerate_pattern
from apps.patterns.services.pattern_builder import build_svg_for_date

from .models import DailyPattern, Motif, Region, SavedPattern, Source


@admin.action(description="Активувати обрані регіони")
def activate_regions(modeladmin, request, queryset):
    queryset.update(is_active=True)


@admin.action(description="Деактивувати обрані регіони")
def deactivate_regions(modeladmin, request, queryset):
    queryset.update(is_active=False)


@admin.register(Source)
class SourceAdmin(ModelAdmin):
    list_display = ("name", "source_type", "publication_year", "region_count", "motif_count")
    list_filter = ("source_type",)
    search_fields = ("name", "author_or_institution")

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .annotate(
                _region_count=Count("region", distinct=True),
                _motif_count=Count("motif", distinct=True),
            )
        )

    @admin.display(description="Регіонів")
    def region_count(self, obj):
        return obj._region_count

    @admin.display(description="Мотивів")
    def motif_count(self, obj):
        return obj._motif_count


@admin.register(Region)
class RegionAdmin(TranslationAdmin, ModelAdmin):
    list_display = ("name", "motif_count", "is_active", "verification_status", "rotation_order")
    list_filter = ("verification_status", "is_active")
    search_fields = ("name",)
    filter_horizontal = ("sources",)
    actions = [activate_regions, deactivate_regions]

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .annotate(_motif_count=Count("compatible_motifs", distinct=True))
        )

    @admin.display(description="Мотивів")
    def motif_count(self, obj):
        return obj._motif_count


@admin.register(Motif)
class MotifAdmin(TranslationAdmin, ModelAdmin):
    list_display = ("name", "verification_status", "is_active")
    list_filter = ("verification_status", "is_active", "compatible_regions")
    filter_horizontal = ("sources", "compatible_regions")


@admin.action(
    description="Примусово перегенерувати (УВАГА: перезапише результат поточною версією алгоритму)"
)
def force_regenerate(modeladmin, request, queryset):
    count = 0
    for pattern in queryset:
        force_regenerate_pattern(pattern, CURRENT_ALGORITHM_VERSION, build_svg_for_date)
        count += 1
    modeladmin.message_user(
        request,
        f"Перегенеровано {count} патернів версією алгоритму {CURRENT_ALGORITHM_VERSION}. "
        "Попередній збережений результат безповоротно замінено.",
        level=messages.WARNING,
    )


@admin.register(DailyPattern)
class DailyPatternAdmin(ModelAdmin):
    list_display = ("date", "region", "algorithm_version", "generation_status")
    list_filter = ("generation_status", "region")
    date_hierarchy = "date"
    filter_horizontal = ("motifs_used",)
    readonly_fields = ("seed", "svg_content", "algorithm_version", "generation_status")
    actions = [force_regenerate]


@admin.register(SavedPattern)
class SavedPatternAdmin(ModelAdmin):
    list_display = ("user", "pattern", "created_at")
    list_filter = ("user",)
