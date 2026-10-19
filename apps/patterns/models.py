import re

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.formats import date_format
from django.utils.translation import gettext as _
from django_ckeditor_5.fields import CKEditor5Field

from apps.core.models import SlugModel, TimeStampedModel


class Source(TimeStampedModel):
    """
    Джерело достовірності контенту.

    Не перекладна модель - джерело існує мовою публікації,
    бібліографічні дані не мають сенсу дублювати різними мовами.
    """

    class SourceType(models.TextChoices):
        ACADEMIC = "academic", "Академічна публікація"
        MUSEUM = "museum", "Музейна колекція"
        INSTITUTION = "institution", "Видання культурної інституції"
        ORAL_TRADITION = "oral_tradition", "Усна традиція (регіональний фольклор)"
        OTHER = "other", "Інше"

    name = models.CharField(
        verbose_name="Назва",
        max_length=255,
        help_text="Книга, музей, наукова публікація тощо.",
    )
    source_type = models.CharField(
        verbose_name="Тип джерела",
        max_length=20,
        choices=SourceType.choices,
        help_text="Від типу залежить рівень довіри до джерела.",
    )
    author_or_institution = models.CharField(
        verbose_name="Автор чи установа",
        max_length=255,
    )
    reference = models.TextField(
        verbose_name="Посилання або бібліографічний запис",
        help_text="URL за наявності, або повний бібліографічний запис для друкованих видань.",
    )
    publication_year = models.PositiveIntegerField(
        verbose_name="Рік",
        null=True,
        blank=True,
        help_text="Рік видання чи публікації (необов'язково).",
    )
    editor_note = models.TextField(
        verbose_name="Примітка редактора",
        blank=True,
        help_text="Чому саме це джерело і чи є розбіжності з іншими.",
    )

    class Meta:
        verbose_name = "Джерело"
        verbose_name_plural = "Джерела"

    def __str__(self):
        return self.name


HEX_COLOR_RE = re.compile(r"#[0-9A-Fa-f]{6}")


def validate_hex_colors(value):
    if not isinstance(value, list) or not all(
        isinstance(c, str) and HEX_COLOR_RE.fullmatch(c) for c in value
    ):
        raise ValidationError('Очікується список кольорів у форматі ["#RRGGBB", ...].')


class RegionQuerySet(models.QuerySet):
    def verified(self):
        """
        Регіони, дозволені до показу в ротації генерації:
        неверифікований запис не потрапляє в активну ротацію - і деактивований
        регіон теж пропускається, навіть якщо формально верифікований.
        """
        return self.filter(
            verification_status=Region.VerificationStatus.VERIFIED,
            is_active=True,
        )


class Region(TimeStampedModel, SlugModel):
    """
    Регіон України. Перекладна назва й опис символіки
    (реєстрація перекладних полів - окремим кроком у translation.py,
    разом із Motif).

    Slug не перекладається, щоб не дублювати canonical-адреси.
    """

    class VerificationStatus(models.TextChoices):
        PENDING = "pending", "На перевірці"
        VERIFIED = "verified", "Верифіковано"
        NEEDS_REVIEW = "needs_review", "Потребує перегляду"

    name = models.CharField(
        verbose_name="Назва",
        max_length=255,
        help_text="Назва регіону, наприклад «Полтавщина».",
    )
    symbolism_description = CKEditor5Field(
        verbose_name="Опис символіки",
        help_text="Розгорнутий опис значення кольорів і мотивів саме цього регіону.",
        config_name="default",
    )
    target_keyword = models.CharField(
        verbose_name="Ключове слово",
        max_length=255,
        blank=True,
        help_text="Цільове ключове слово/фраза для цієї сторінки (SEO).",
    )
    seo_title = models.CharField(
        verbose_name="SEO title",
        max_length=70,
        blank=True,
        help_text="Заголовок сторінки для пошукових систем. Автоматично додає: - VyshyvankaDaily",
    )
    seo_description = models.CharField(
        verbose_name="SEO description",
        max_length=160,
        blank=True,
        help_text="Опис сторінки для пошукових систем (SEO). Порожнє - береться з опису символіки.",
    )
    dominant_colors = models.JSONField(
        verbose_name="Кольори генератора",
        validators=[validate_hex_colors],
        help_text='Список кольорових кодів (наприклад, ["#FF6B35", "#004E89"]).',
    )
    accent_colors = models.JSONField(
        verbose_name="Також трапляються",
        default=list,
        blank=True,
        validators=[validate_hex_colors],
        help_text="Кольори, що також трапляються. Лише для показу, на генерацію не впливають.",
    )
    generator_only_colors = models.JSONField(
        verbose_name="Лише в генераторі",
        default=list,
        blank=True,
        validators=[validate_hex_colors],
        help_text="Кольори генератора без підтвердження в джерелах: на сторінці не показуються.",
    )
    shirt_cut_type = models.CharField(
        verbose_name="Крій сорочки",
        max_length=255,
        blank=True,
        help_text="Лише інформаційне поле, на генерацію не впливає.",
    )
    rotation_order = models.IntegerField(
        verbose_name="Порядок у ротації",
        help_text="Позиція регіону в щоденній ротації.",
    )
    is_active = models.BooleanField(
        verbose_name="Активний",
        default=True,
        help_text="Дозволяє тимчасово виключити регіон з ротації без видалення даних.",
    )
    sources = models.ManyToManyField(
        "patterns.Source",
        verbose_name="Джерела",
        help_text="Обов'язково: без джерел регіон не публікується.",
    )
    verification_status = models.CharField(
        verbose_name="Статус перевірки",
        max_length=20,
        choices=VerificationStatus.choices,
        default=VerificationStatus.PENDING,
        help_text="У ротацію потрапляють лише верифіковані регіони.",
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

        for field in ("symbolism_description_uk", "symbolism_description_en"):
            value = getattr(self, field)
            if value:
                setattr(
                    self,
                    field,
                    bleach.clean(
                        value,
                        tags=settings.ALLOWED_BLOG_HTML_TAGS,
                        attributes=settings.ALLOWED_BLOG_HTML_ATTRIBUTES,
                        strip=True,
                    ),
                )
        super().save(*args, **kwargs)

    def get_claim_type(self) -> str:
        """
        Тип твердження для позначки на сторінці:
        "задокументоване", якщо є хоча б одне джерело високого рівня
        довіри; інакше "за усною традицією". Не окреме поле моделі -
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

    def get_absolute_url(self):
        from django.urls import reverse

        return reverse("patterns:region_detail", args=[self.slug])

    @property
    def short_name(self):
        from .region_groups import short_name

        return short_name(self)

    @property
    def stripe_colors(self):
        colors = []
        for color in self.shown_colors + list(self.accent_colors or []):
            if color not in colors:
                colors.append(color)
        return colors[:6]

    @property
    def shown_colors(self):
        hidden = set(self.generator_only_colors or [])
        return [c for c in self.dominant_colors or [] if c not in hidden]

    def __str__(self):
        return self.name

    @property
    def published_blog_posts(self):
        """
        Лише опубліковані статті. Фільтр саме тут, а не в шаблоні:
        так чернетка не потрапить на публічну сторінку навіть якщо
        десь забути умову в розмітці.
        """
        from django.db.models import Q

        from apps.blog.models import BlogPost

        mentions = Q(related_region=self) | Q(body__contains=f"/regions/{self.slug}/")
        return (
            BlogPost.objects.filter(mentions, status="published")
            .select_related("category")
            .order_by("-published_at")
        )


class MotifQuerySet(models.QuerySet):
    def verified(self):
        """Мотиви, дозволені до використання в генерації."""
        return self.filter(
            verification_status=Motif.VerificationStatus.VERIFIED,
            is_active=True,
        )


class Motif(TimeStampedModel):
    """
    Довідник геометричних елементів орнаменту. Перекладна модель.

    Без власного slug: окремої сторінки в мотиву немає.
    """

    class VerificationStatus(models.TextChoices):
        PENDING = "pending", "На перевірці"
        VERIFIED = "verified", "Верифіковано"
        NEEDS_REVIEW = "needs_review", "Потребує перегляду"

    name = models.CharField(
        verbose_name="Назва",
        max_length=255,
        help_text="Назва мотиву, наприклад «Ромб», «Барвінок».",
    )
    meaning_description = models.TextField(
        verbose_name="Значення",
        help_text="Коротке пояснення що символізує мотив.",
    )
    geometry_parameters = models.JSONField(
        verbose_name="Геометрія",
        help_text="Сітка мотиву у форматі pixel_grid_v1 (ключі grid і palette).",
    )
    compatible_regions = models.ManyToManyField(
        "patterns.Region",
        verbose_name="Регіони",
        blank=True,
        related_name="compatible_motifs",
        help_text="Які регіони типово використовують цей мотив.",
    )
    sources = models.ManyToManyField(
        "patterns.Source",
        verbose_name="Джерела",
        help_text="Обов'язково, як і в регіону.",
    )
    verification_status = models.CharField(
        verbose_name="Статус перевірки",
        max_length=20,
        choices=VerificationStatus.choices,
        default=VerificationStatus.PENDING,
        help_text="У генерацію потрапляють лише верифіковані мотиви.",
    )
    is_active = models.BooleanField(verbose_name="Активний", default=True)

    objects = MotifQuerySet.as_manager()

    class Meta:
        verbose_name = "Мотив"
        verbose_name_plural = "Мотиви"

    def __str__(self):
        return self.name


class DailyPattern(TimeStampedModel):
    """
    Центральна модель проєкту - щоденний згенерований патерн.

    SVG зберігається як текст у базі, не файл: простий бекап і незалежність
    від ефемерної файлової системи хостингу.
    """

    class GenerationStatus(models.TextChoices):
        SUCCESS = "success", "Успішно"
        FALLBACK = "fallback", "Помилка, застосовано резервний варіант"

    date = models.DateField(
        verbose_name="Дата",
        unique=True,
        db_index=True,
        help_text="Один патерн на календарний день.",
    )
    region = models.ForeignKey(
        "patterns.Region",
        verbose_name="Регіон",
        on_delete=models.PROTECT,
        related_name="daily_patterns",
        help_text="Регіон не можна видалити, поки є пов'язані патерни.",
    )
    seed = models.CharField(
        verbose_name="Seed",
        max_length=255,
        help_text="Детермінований seed на основі дати.",
    )
    algorithm_version = models.PositiveIntegerField(
        verbose_name="Версія алгоритму",
        help_text="Старі патерни лишаються на версії генератора, якою їх створено.",
    )
    svg_content = models.TextField(
        verbose_name="SVG",
        help_text="Готовий SVG, кеш генерації.",
    )
    motifs_used = models.ManyToManyField(
        "patterns.Motif",
        verbose_name="Мотиви",
        blank=True,
        related_name="daily_patterns",
        help_text="Які мотиви увійшли до патерну.",
    )
    generation_status = models.CharField(
        verbose_name="Статус генерації",
        max_length=20,
        choices=GenerationStatus.choices,
        default=GenerationStatus.SUCCESS,
        help_text="Резервний варіант означає помилку генерації.",
    )

    @property
    def breadcrumbs(self):
        from django.urls import reverse

        return [
            {"label": _("Регіони"), "url": reverse("patterns:region_list")},
            {
                "label": self.region.name,
                "url": reverse("patterns:region_detail", args=[self.region.slug]),
            },
            {"label": date_format(self.date, "j E Y")},
        ]

    class Meta:
        verbose_name = "Щоденний патерн"
        verbose_name_plural = "Щоденні патерни"
        ordering = ["-date"]

    def __str__(self):
        return f"{self.date} - {self.region}"


class SavedPattern(TimeStampedModel):
    """Збережений патерн користувача, колекція."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="Користувач",
        on_delete=models.CASCADE,
        related_name="saved_patterns",
    )
    pattern = models.ForeignKey(
        "patterns.DailyPattern",
        verbose_name="Патерн",
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
        return f"{self.user} - {self.pattern}"


class RegionPhoto(TimeStampedModel):
    """
    Реальне фото вишиванки регіону (не згенерований орнамент) - плівка
    мініатюр на сторінці регіону, повний розмір по кліку. Окремо від
    DailyPattern: це фотографії, підібрані вручну, з перевіреним
    джерелом/ліцензією, не автоматична генерація.
    """

    region = models.ForeignKey(
        "patterns.Region",
        verbose_name="Регіон",
        on_delete=models.CASCADE,
        related_name="photos",
    )
    thumbnail_url = models.URLField(
        verbose_name="Мініатюра (URL)",
        help_text="Маленьке зображення для плівки мініатюр на сторінці регіону.",
    )
    image_url = models.URLField(
        verbose_name="Зображення (URL)",
        help_text="Повнорозмірне зображення, що відкривається по кліку.",
    )
    caption = models.CharField(verbose_name="Підпис", max_length=255, blank=True)
    source_note = models.CharField(
        verbose_name="Джерело",
        max_length=255,
        blank=True,
        help_text="Джерело/ліцензія фото - автор чи звідки взято. Перевір права на використання.",
    )
    order = models.PositiveIntegerField(verbose_name="Порядок", default=0)
    is_active = models.BooleanField(verbose_name="Показувати", default=True)

    class Meta:
        verbose_name = "Фото регіону"
        verbose_name_plural = "Фото регіону"
        ordering = ["order", "id"]

    def __str__(self):
        return f"{self.region.name} - фото {self.pk}"

    @property
    def alt_text(self):
        """Короткий alt з першого речення підпису; повний підпис лишається під фото."""
        label, sep, rest = self.caption.partition(": ")
        first = (rest if sep and len(label) < 40 else self.caption).split(". ")[0].rstrip(".")
        prefix = f"{label.split()[0]}: " if sep and self.is_illustration else ""
        text = f"{prefix}{first}"
        return text if len(text) <= 100 else text[:97].rsplit(" ", 1)[0] + "..."

    @property
    def is_illustration(self):
        return self.source_note.startswith("Ілюстрація")
