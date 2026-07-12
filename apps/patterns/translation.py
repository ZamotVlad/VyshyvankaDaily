from modeltranslation.translator import TranslationOptions, register

from .models import Motif, Region


@register(Region)
class RegionTranslationOptions(TranslationOptions):
    fields = ("name", "symbolism_description")


@register(Motif)
class MotifTranslationOptions(TranslationOptions):
    fields = ("name", "meaning_description")
