from django.contrib import admin
from modeltranslation.admin import TranslationAdmin
from unfold.admin import ModelAdmin, TabularInline

from .models import FAQCategory, FAQItem


class FAQItemInline(TabularInline):
    model = FAQItem
    extra = 1


@admin.register(FAQCategory)
class FAQCategoryAdmin(ModelAdmin):
    list_display = ("name", "order")
    inlines = [FAQItemInline]


@admin.register(FAQItem)
class FAQItemAdmin(TranslationAdmin, ModelAdmin):
    list_display = ("question", "category", "order")
    list_filter = ("category",)
