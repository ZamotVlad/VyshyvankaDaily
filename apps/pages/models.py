from django.db import models

from apps.core.models import SlugModel, TimeStampedModel


class StaticPage(TimeStampedModel, SlugModel):
    """Статична сторінка (розділ 3.10 ТЗ) — перекладна, WYSIWYG-тіло."""

    title = models.CharField(max_length=255)
    body = models.TextField(help_text="HTML-вміст.")

    slug_source_field = "title_uk"

    class Meta:
        verbose_name = "Статична сторінка"
        verbose_name_plural = "Статичні сторінки"

    def __str__(self):
        return self.title


class FAQCategory(TimeStampedModel):
    """Категорія для групування пунктів FAQ."""

    name = models.CharField(max_length=255)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = "Категорія FAQ"
        verbose_name_plural = "Категорії FAQ"
        ordering = ["order"]

    def __str__(self):
        return self.name


class FAQItem(TimeStampedModel):
    """Пункт частих запитань (розділ 3.10 ТЗ) — перекладний, згрупований, впорядкований."""

    category = models.ForeignKey(FAQCategory, on_delete=models.CASCADE, related_name="items")
    question = models.CharField(max_length=255)
    answer = models.TextField()
    order = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = "Пункт FAQ"
        verbose_name_plural = "Пункти FAQ"
        ordering = ["category__order", "order"]

    def __str__(self):
        return self.question
