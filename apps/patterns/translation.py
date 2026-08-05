from modeltranslation.translator import TranslationOptions, register

from .models import Motif, Region, RegionPhoto


@register(Region)
class RegionTranslationOptions(TranslationOptions):
    fields = ("name", "target_keyword", "seo_title", "seo_description")


@register(Motif)
class MotifTranslationOptions(TranslationOptions):
    fields = ("name", "meaning_description")


@register(RegionPhoto)
class RegionPhotoTranslationOptions(TranslationOptions):
    fields = ("caption",)
