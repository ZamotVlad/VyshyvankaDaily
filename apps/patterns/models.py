from django.conf import settings
from django.db import models
from django.utils.translation import gettext as _
from django_ckeditor_5.fields import CKEditor5Field

from apps.core.models import SlugModel, TimeStampedModel


class Source(TimeStampedModel):
    """
    Джерело достовірності контенту (розділ 3.4, 4.2 ТЗ).

    Не перекладна модель (розділ 3.11 ТЗ) — джерело існує мовою публікації,
    бібліографічні дані не мають сенсу дублювати різними мовами.
    """

    class SourceType(models.TextChoices):
        ACADEMIC = "academic", "Академічна публікація"
        MUSEUM = "museum", "Музейна колекція"
        INSTITUTION = "institution", "Видання культурної інституції"
        ORAL_TRADITION = "oral_tradition", "Усна традиція (регіональний фольклор)"
        OTHER = "other", "Інше"

    name = models.CharField(
        max_length=255,
        help_text="Назва джерела — книга, музей, наукова публікація тощо.",
    )
    source_type = models.CharField(
        max_length=20,
        choices=SourceType.choices,
        help_text="Рівень довіри визначається типом джерела (розділ 4.2 ТЗ).",
    )
    author_or_institution = models.CharField(
        max_length=255,
        help_text="Автор чи установа.",
    )
    reference = models.TextField(
        help_text="URL за наявності, або повний бібліографічний запис для друкованих видань.",
    )
    publication_year = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Рік видання чи публікації (необов'язково).",
    )
    editor_note = models.TextField(
        blank=True,
        help_text=(
            "Коротке пояснення чому саме це джерело використано, "
            "чи є розбіжності з іншими джерелами (розділ 3.4 ТЗ)."
        ),
    )

    class Meta:
        verbose_name = "Джерело"
        verbose_name_plural = "Джерела"

    def __str__(self):
        return self.name


class RegionQuerySet(models.QuerySet):
    def verified(self):
        """
        Регіони, дозволені до показу в ротації генерації (розділ 4.4 ТЗ):
        неверифікований запис не потрапляє в активну ротацію — і деактивований
        регіон теж пропускається (розділ 8.3 ТЗ), навіть якщо формально верифікований.
        """
        return self.filter(
            verification_status=Region.VerificationStatus.VERIFIED,
            is_active=True,
        )


class Region(TimeStampedModel, SlugModel):
    """
    Регіон України (розділ 3.2 ТЗ). Перекладна назва й опис символіки
    (реєстрація перекладних полів — окремим кроком у translation.py,
    разом із Motif).

    Slug НЕ перекладається (явна вимога розділу 3.2 ТЗ) — уникнення
    дублювання canonical-адрес.
    """

    class VerificationStatus(models.TextChoices):
        PENDING = "pending", "На перевірці"
        VERIFIED = "verified", "Верифіковано"
        NEEDS_REVIEW = "needs_review", "Потребує перегляду"

    name = models.CharField(
        max_length=255,
        help_text="Назва регіону, наприклад «Полтавщина».",
    )
    symbolism_description = CKEditor5Field(
        help_text="Розгорнутий опис значення кольорів і мотивів саме цього регіону.",
        config_name="default",
    )
    target_keyword = models.CharField(
        max_length=255,
        blank=True,
        help_text="Цільове ключове слово/фраза для цієї сторінки (SEO).",
    )
    seo_title = models.CharField(
        max_length=70,
        blank=True,
        help_text="Заголовок сторінки для пошукових систем. Автоматично додає: - VyshyvankaDaily",
    )
    seo_description = models.CharField(
        max_length=160,
        blank=True,
        help_text="Опис сторінки для пошукових систем (SEO). Порожнє - береться з опису символіки.",
    )
    dominant_colors = models.JSONField(
        help_text='Список кольорових кодів (наприклад, ["#FF6B35", "#004E89"]).',
    )
    shirt_cut_type = models.CharField(
        max_length=255,
        blank=True,
        help_text="Особливості крою сорочки (наразі інформаційне поле).",
    )
    rotation_order = models.IntegerField(
        help_text="Позиція регіону в календарній послідовності ротації (розділ 8.3 ТЗ).",
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Дозволяє тимчасово виключити регіон з ротації без видалення даних.",
    )
    sources = models.ManyToManyField(
        "patterns.Source",
        help_text="Обов'язкове — порожній перелік джерел блокує публікацію (розділ 4.4 ТЗ).",
    )
    verification_status = models.CharField(
        max_length=20,
        choices=VerificationStatus.choices,
        default=VerificationStatus.PENDING,
        help_text="Редакційний статус (розділ 4.4 ТЗ).",
    )

    slug_source_field = "name_uk"

    objects = RegionQuerySet.as_manager()

    class Meta:
        verbose_name = "Регіон"
        verbose_name_plural = "Регіони"
        ordering = ["rotation_order"]

    def save(self, *args, **kwargs):
        import bleach
        from django.conf import settings

        self.symbolism_description = bleach.clean(
            self.symbolism_description,
            tags=settings.ALLOWED_BLOG_HTML_TAGS,
            attributes=settings.ALLOWED_BLOG_HTML_ATTRIBUTES,
            strip=True,
        )
        super().save(*args, **kwargs)

    def get_claim_type(self) -> str:
        """
        Тип твердження для позначки на сторінці (розділ 4.3 ТЗ):
        "задокументоване", якщо є хоча б одне джерело високого рівня
        довіри; інакше "за усною традицією". Не окреме поле моделі —
        виводиться з наявних Source, щоб уникнути розсинхронізації
        між полем і реальними джерелами.
        """
        high_trust_types = {
            Source.SourceType.ACADEMIC,
            Source.SourceType.MUSEUM,
            Source.SourceType.INSTITUTION,
        }
        if self.sources.filter(source_type__in=high_trust_types).exists():
            return "documented"
        return "oral_tradition"

    @property
    def breadcrumbs(self):
        from django.urls import reverse

        return [
            {"label": _("Регіони"), "url": reverse("patterns:region_list")},
            {"label": self.name},
        ]

    def __str__(self):
        return self.name

    @property
    def published_blog_posts(self):
        """
        Лише опубліковані статті. Фільтр саме тут, а не в шаблоні:
        так чернетка не потрапить на публічну сторінку навіть якщо
        десь забути умову в розмітці.
        """
        return self.blog_posts.filter(status="published")


class MotifQuerySet(models.QuerySet):
    def verified(self):
        """Мотиви, дозволені до використання в генерації (розділ 4.4 ТЗ)."""
        return self.filter(
            verification_status=Motif.VerificationStatus.VERIFIED,
            is_active=True,
        )


class Motif(TimeStampedModel):
    """
    Довідник геометричних елементів орнаменту (розділ 3.3 ТЗ). Перекладна модель.

    Без власного slug — ТЗ (розділ 3.3) не згадує ЧПУ-адресу для мотиву,
    на відміну від Region.
    """

    class VerificationStatus(models.TextChoices):
        PENDING = "pending", "На перевірці"
        VERIFIED = "verified", "Верифіковано"
        NEEDS_REVIEW = "needs_review", "Потребує перегляду"

    name = models.CharField(
        max_length=255,
        help_text="Назва мотиву, наприклад «Ромб», «Барвінок».",
    )
    meaning_description = models.TextField(
        help_text="Коротке пояснення що символізує мотив.",
    )
    geometry_parameters = models.JSONField(
        help_text=(
            "Базові координати, правила симетрії, застосовні групи симетрії (розділ 3.3, 8.4 ТЗ)."
        ),
    )
    compatible_regions = models.ManyToManyField(
        "patterns.Region",
        blank=True,
        related_name="compatible_motifs",
        help_text="Які регіони типово використовують цей мотив.",
    )
    sources = models.ManyToManyField(
        "patterns.Source",
        help_text="Обов'язкове — той самий принцип, що й у Region (розділ 4.4 ТЗ).",
    )
    verification_status = models.CharField(
        max_length=20,
        choices=VerificationStatus.choices,
        default=VerificationStatus.PENDING,
        help_text="Той самий принцип, що й у Region (розділ 3.3, 4.4 ТЗ).",
    )
    is_active = models.BooleanField(default=True)

    objects = MotifQuerySet.as_manager()

    class Meta:
        verbose_name = "Мотив"
        verbose_name_plural = "Мотиви"

    def __str__(self):
        return self.name


class DailyPattern(TimeStampedModel):
    """
    Центральна модель проєкту (розділ 3.5 ТЗ) — щоденний згенерований патерн.

    SVG зберігається як текст у базі, не файл (обґрунтування — розділ 3.5 ТЗ:
    легкість бекапу, незалежність від файлової системи хостингу).
    """

    class GenerationStatus(models.TextChoices):
        SUCCESS = "success", "Успішно"
        FALLBACK = "fallback", "Помилка, застосовано резервний варіант"

    date = models.DateField(
        unique=True,
        db_index=True,
        help_text="Один патерн на календарний день.",
    )
    region = models.ForeignKey(
        "patterns.Region",
        on_delete=models.PROTECT,
        related_name="daily_patterns",
        help_text="Заборона видалення регіону поки є пов'язані патерни.",
    )
    seed = models.CharField(
        max_length=255,
        help_text="Детермінований seed на основі дати (розділ 8.2 ТЗ).",
    )
    algorithm_version = models.PositiveIntegerField(
        help_text=(
            "Критично для відтворюваності — історичні патерни лишаються "
            "прив'язаними до версії, якою вони були створені (розділ 8.8 ТЗ)."
        ),
    )
    svg_content = models.TextField(
        help_text="Готовий результат генерації — текстовий XML-вміст SVG.",
    )
    motifs_used = models.ManyToManyField(
        "patterns.Motif",
        blank=True,
        related_name="daily_patterns",
        help_text="Які саме мотиви увійшли до патерну — для аналітики й фільтрів.",
    )
    generation_status = models.CharField(
        max_length=20,
        choices=GenerationStatus.choices,
        default=GenerationStatus.SUCCESS,
        help_text="Службове поле для діагностики (розділ 8.6 ТЗ).",
    )

    @property
    def breadcrumbs(self):
        from django.urls import reverse

        return [
            {"label": _("Архів"), "url": reverse("patterns:archive")},
            {
                "label": self.region.name,
                "url": reverse("patterns:region_detail", args=[self.region.slug]),
            },
            {"label": str(self.date)},
        ]

    class Meta:
        verbose_name = "Щоденний патерн"
        verbose_name_plural = "Щоденні патерни"
        ordering = ["-date"]

    def __str__(self):
        return f"{self.date} — {self.region}"


class SavedPattern(TimeStampedModel):
    """Збережений патерн користувача, колекція (розділ 3.6 ТЗ)."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="saved_patterns",
    )
    pattern = models.ForeignKey(
        "patterns.DailyPattern",
        on_delete=models.CASCADE,
        related_name="saved_by",
    )

    class Meta:
        verbose_name = "Збережений патерн"
        verbose_name_plural = "Збережені патерни"
        constraints = [
            models.UniqueConstraint(
                fields=["user", "pattern"],
                name="unique_user_pattern",
            )
        ]

    def __str__(self):
        return f"{self.user} — {self.pattern}"


class RegionPhoto(TimeStampedModel):
    """
    Реальне фото вишиванки регіону (не згенерований орнамент) - плівка
    мініатюр на сторінці регіону, повний розмір по кліку. Окремо від
    DailyPattern: це фотографії, підібрані вручну, з перевіреним
    джерелом/ліцензією, не автоматична генерація.
    """

    region = models.ForeignKey(
        "patterns.Region",
        on_delete=models.CASCADE,
        related_name="photos",
    )
    thumbnail_url = models.URLField(
        help_text="Маленьке зображення для плівки мініатюр на сторінці регіону.",
    )
    image_url = models.URLField(
        help_text="Повнорозмірне зображення, що відкривається по кліку.",
    )
    caption = models.CharField(max_length=255, blank=True)
    source_note = models.CharField(
        max_length=255,
        blank=True,
        help_text="Джерело/ліцензія фото - автор чи звідки взято. Перевір права на використання.",
    )
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Фото регіону"
        verbose_name_plural = "Фото регіону"
        ordering = ["order", "id"]

    def __str__(self):
        return f"{self.region.name} - фото {self.pk}"
