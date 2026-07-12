from django.contrib import admin
from modeltranslation.admin import TranslationAdmin

from .models import DailyPattern, Motif, Region, SavedPattern, Source


@admin.register(Source)
class SourceAdmin(admin.ModelAdmin):
    list_display = ("name", "source_type", "publication_year")
    list_filter = ("source_type",)
    search_fields = ("name", "author_or_institution")


@admin.register(Region)
class RegionAdmin(TranslationAdmin):
    list_display = ("name", "rotation_order", "verification_status", "is_active")
    list_filter = ("verification_status", "is_active")
    filter_horizontal = ("sources",)


@admin.register(Motif)
class MotifAdmin(TranslationAdmin):
    list_display = ("name", "verification_status", "is_active")
    list_filter = ("verification_status", "is_active")
    filter_horizontal = ("sources", "compatible_regions")


@admin.register(DailyPattern)
class DailyPatternAdmin(admin.ModelAdmin):
    list_display = ("date", "region", "algorithm_version", "generation_status")
    list_filter = ("generation_status", "region")
    date_hierarchy = "date"
    filter_horizontal = ("motifs_used",)


@admin.register(SavedPattern)
class SavedPatternAdmin(admin.ModelAdmin):
    list_display = ("user", "pattern", "created_at")
    list_filter = ("user",)
