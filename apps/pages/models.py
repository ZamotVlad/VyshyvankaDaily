from django.db import models

from apps.core.models import SlugModel, TimeStampedModel


class StaticPage(TimeStampedModel, SlugModel):
    """Статична сторінка - перекладна, WYSIWYG-тіло."""

    title = models.CharField(verbose_name="Заголовок", max_length=255)
    body = models.TextField(verbose_name="Текст", help_text="HTML-розмітка.")

    slug_source_field = "title_uk"

    class Meta:
        verbose_name = "Статична сторінка"
        verbose_name_plural = "Статичні сторінки"

    def __str__(self):
        return self.title


class FAQCategory(TimeStampedModel):
    """Категорія для групування пунктів FAQ."""

    name = models.CharField(verbose_name="Назва", max_length=255)
    order = models.PositiveIntegerField(verbose_name="Порядок", default=0)

    class Meta:
        verbose_name = "Категорія FAQ"
        verbose_name_plural = "Категорії FAQ"
        ordering = ["order"]

    def __str__(self):
        return self.name


class FAQItem(TimeStampedModel):
    """Пункт частих запитань - перекладний, згрупований, впорядкований."""

    category = models.ForeignKey(
        FAQCategory, verbose_name="Категорія", on_delete=models.CASCADE, related_name="items"
    )
    question = models.CharField(verbose_name="Питання", max_length=255)
    answer = models.TextField(
        verbose_name="Відповідь",
    )
    order = models.PositiveIntegerField(verbose_name="Порядок", default=0)

    class Meta:
        verbose_name = "Пункт FAQ"
        verbose_name_plural = "Пункти FAQ"
        ordering = ["category__order", "order"]

    def __str__(self):
        return self.question
