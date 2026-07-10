from django.db import models
from slugify import slugify as translit_slugify


class TimeStampedModel(models.Model):
    """Абстрактна модель з полями часу створення й оновлення."""

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class SlugModel(models.Model):
    """
    Абстрактна модель з ЧПУ-полем (розділ 3.1 ТЗ).

    Ручний slug — основний спосіб (ADR 1, DECISIONS.md).
    Якщо slug не заданий вручну — автоматична транслітерація один раз
    при першому збереженні, з поля-джерела (перевизначається в нащадку
    через `slug_source_field`).

    allow_unicode=False прописано ЯВНО (а не залишено на дефолт SlugField),
    бо ТЗ вимагає щоб це рішення читалось у коді, а не малось на увазі:
    slug має складатись виключно з латинських символів незалежно від мови
    інтерфейсу, щоб уникнути потворного %-кодування в URL.
    """

    slug = models.SlugField(max_length=255, unique=True, blank=True, allow_unicode=False)

    slug_source_field = "name"

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        if not self.slug:
            source_value = getattr(self, self.slug_source_field, "")
            self.slug = translit_slugify(source_value)
        super().save(*args, **kwargs)
