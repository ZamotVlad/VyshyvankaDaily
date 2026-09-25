from django.contrib import admin
from modeltranslation.admin import TranslationAdmin, TranslationTabularInline
from unfold.admin import ModelAdmin, TabularInline

from .models import FAQCategory, FAQItem


class FAQItemInline(TranslationTabularInline, TabularInline):
    model = FAQItem
    extra = 1


@admin.register(FAQCategory)
class FAQCategoryAdmin(TranslationAdmin, ModelAdmin):
    list_display = ("name", "order")
    inlines = [FAQItemInline]


@admin.register(FAQItem)
class FAQItemAdmin(TranslationAdmin, ModelAdmin):
    list_display = ("question", "category", "order")
    list_filter = ("category",)
