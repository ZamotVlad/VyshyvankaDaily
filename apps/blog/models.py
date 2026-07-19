from django.conf import settings
from django.db import models
from django_ckeditor_5.fields import CKEditor5Field

from apps.core.models import SlugModel, TimeStampedModel


class BlogCategory(TimeStampedModel, SlugModel):
    """Категорія блогу (розділ 3.8 ТЗ). Перекладна."""

    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    slug_source_field = "name_uk"

    class Meta:
        verbose_name = "Категорія блогу"
        verbose_name_plural = "Категорії блогу"

    def __str__(self):
        return self.name


class BlogPost(TimeStampedModel, SlugModel):
    """Стаття блогу (розділ 3.8 ТЗ). Перекладна, з WYSIWYG-тілом."""

    class Status(models.TextChoices):
        DRAFT = "draft", "Чернетка"
        PUBLISHED = "published", "Опубліковано"

    class PostType(models.TextChoices):
        EDITORIAL = "editorial", "Редакційна"
        GUEST = "guest", "Гостьова"
        SPONSORED = "sponsored", "Спонсорована"

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="blog_posts",
    )
    title = models.CharField(max_length=255, db_index=True)
    excerpt = models.TextField(help_text="Короткий опис для карток у списку статей.")
    body = CKEditor5Field(
        help_text="HTML-вміст, санітизується при збереженні.",
        config_name="default",
    )
    cover_image_url = models.URLField(blank=True)
    category = models.ForeignKey(
        BlogCategory,
        on_delete=models.PROTECT,
        related_name="posts",
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
    )
    post_type = models.CharField(
        max_length=20,
        choices=PostType.choices,
        default=PostType.EDITORIAL,
        help_text="Визначає позначку «Партнерський матеріал» для непередакційного типу.",
    )
    guest_author_name = models.CharField(
        max_length=255,
        blank=True,
        help_text="Заповнюється лише для гостьових/спонсорованих публікацій.",
    )
    submitter_contact = models.CharField(
        max_length=255,
        blank=True,
        help_text="Службове поле, не публічне.",
    )
    sources = models.ManyToManyField(
        "patterns.Source",
        blank=True,
        related_name="blog_posts",
        help_text=(
            "Обов'язково для статей, що торкаються історичних/символічних "
            "тверджень (розділ 4.6 ТЗ)."
        ),
    )
    published_at = models.DateTimeField(null=True, blank=True)
    view_count = models.PositiveIntegerField(default=0)
    seo_title = models.CharField(max_length=255, blank=True)
    seo_description = models.TextField(blank=True)

    slug_source_field = "title_uk"

    def save(self, *args, **kwargs):
        import bleach

        self.body = bleach.clean(
            self.body,
            tags=settings.ALLOWED_BLOG_HTML_TAGS,
            attributes=settings.ALLOWED_BLOG_HTML_ATTRIBUTES,
            strip=True,
        )
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Стаття блогу"
        verbose_name_plural = "Статті блогу"
        ordering = ["-published_at"]

    def __str__(self):
        return self.title


class GuestPostSubmission(TimeStampedModel):
    """Заявка на гостьовий пост (розділ 3.9 ТЗ)."""

    class ReviewStatus(models.TextChoices):
        NEW = "new", "Нова"
        IN_REVIEW = "in_review", "На розгляді"
        APPROVED = "approved", "Схвалено"
        REJECTED = "rejected", "Відхилено"

    contact_name = models.CharField(max_length=255)
    email = models.EmailField()
    brand_name = models.CharField(max_length=255, blank=True)
    proposed_topic = models.CharField(max_length=255)
    proposal_description = models.TextField()
    honeypot = models.CharField(
        max_length=255,
        blank=True,
        help_text="Приховане поле проти автоматичного спаму — має лишатись порожнім.",
    )
    submitter_ip = models.GenericIPAddressField(null=True, blank=True)
    review_status = models.CharField(
        max_length=20,
        choices=ReviewStatus.choices,
        default=ReviewStatus.NEW,
    )

    class Meta:
        verbose_name = "Заявка на гостьовий пост"
        verbose_name_plural = "Заявки на гостьові пости"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.contact_name} — {self.proposed_topic}"
