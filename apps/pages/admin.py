from django.contrib import admin
from django.db.models import Count
from modeltranslation.admin import TranslationAdmin, TranslationTabularInline
from unfold.admin import ModelAdmin, TabularInline

from .models import FAQCategory, FAQItem, StaticPage


@admin.register(StaticPage)
class StaticPageAdmin(TranslationAdmin, ModelAdmin):
    list_display = ("title", "slug", "updated_at")
    search_fields = ("title_uk", "title_en", "slug")
    prepopulated_fields = {"slug": ("title_uk",)}


class FAQItemInline(TranslationTabularInline, TabularInline):
    model = FAQItem
    extra = 0


@admin.register(FAQCategory)
class FAQCategoryAdmin(TranslationAdmin, ModelAdmin):
    list_display = ("name", "order", "item_count")
    list_editable = ("order",)
    inlines = [FAQItemInline]

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(_items=Count("items"))

    @admin.display(description="Питань", ordering="_items")
    def item_count(self, obj):
        return obj._items


@admin.register(FAQItem)
class FAQItemAdmin(TranslationAdmin, ModelAdmin):
    list_display = ("question", "category", "order")
    list_editable = ("order",)
    list_filter = ("category",)
    list_select_related = ("category",)
    search_fields = ("question_uk", "question_en", "answer_uk", "answer_en")
