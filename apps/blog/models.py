import re

from django.conf import settings
from django.db import models
from django.utils.html import strip_tags
from django.utils.translation import get_language, gettext_lazy
from django.utils.translation import gettext as _
from django_ckeditor_5.fields import CKEditor5Field

from apps.core.models import SlugModel, TimeStampedModel


class Author(TimeStampedModel, SlugModel):
    """
    Автор контенту сайту (статті блогу, описи регіонів). Редагується
    виключно через адмінку - навмисно немає жодної публічної форми чи
    поля на профілі звичайного користувача, щоб уникнути плутанини з
    accounts.Profile (те, що бачить кожен зареєстрований відвідувач).
    """

    name = models.CharField(verbose_name="Ім'я", max_length=255)
    bio = models.TextField(verbose_name="Біографія", blank=True)
    avatar_url = models.URLField(verbose_name="Фото (URL)", blank=True)
    website_url = models.URLField(verbose_name="Сайт", blank=True)

    slug_source_field = "name_uk"

    def get_absolute_url(self):
        from django.urls import reverse

        return reverse("blog:author_detail", args=[self.slug])

    class Meta:
        verbose_name = "Автор"
        verbose_name_plural = "Автори"

    def __str__(self):
        return self.name


class BlogCategory(TimeStampedModel, SlugModel):
    """Категорія блогу. Перекладна."""

    name = models.CharField(verbose_name="Назва", max_length=255)
    description = models.TextField(verbose_name="Опис", blank=True)
    is_active = models.BooleanField(verbose_name="Активна", default=True)

    slug_source_field = "name_uk"

    class Meta:
        verbose_name = "Категорія блогу"
        verbose_name_plural = "Категорії блогу"

    def __str__(self):
        return self.name


class BlogPost(TimeStampedModel, SlugModel):
    """Стаття блогу. Перекладна, з WYSIWYG-тілом."""

    class Status(models.TextChoices):
        DRAFT = "draft", "Чернетка"
        PUBLISHED = "published", "Опубліковано"

    class PostType(models.TextChoices):
        EDITORIAL = "editorial", "Редакційна"
        GUEST = "guest", "Гостьова"
        SPONSORED = "sponsored", "Спонсорована"

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="Користувач",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="blog_posts",
    )
    blog_author = models.ForeignKey(
        "blog.Author",
        verbose_name="Автор",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="posts",
        help_text="Публічно видимий автор статті (плашка на сторінці, сторінка автора).",
    )
    title = models.CharField(verbose_name="Заголовок (H1)", max_length=255, db_index=True)
    excerpt = models.TextField(
        verbose_name="Короткий опис", help_text="Короткий опис для карток у списку статей."
    )
    body = CKEditor5Field(
        verbose_name="Текст",
        help_text="HTML-вміст, санітизується при збереженні.",
        config_name="default",
    )
    body_en = CKEditor5Field(
        verbose_name="Текст (EN)",
        blank=True,
        default="",
        help_text="Англійський текст статті. Порожній - EN-версія не індексується.",
        config_name="default",
    )
    cover_image_url = models.URLField(verbose_name="Обкладинка (URL)", blank=True)
    cover_image_alt = models.CharField(
        verbose_name="Alt обкладинки",
        max_length=255,
        blank=True,
        help_text="Що зображено на обкладинці. Не повторювати заголовок статті.",
    )
    category = models.ForeignKey(
        BlogCategory,
        verbose_name="Категорія",
        on_delete=models.PROTECT,
        related_name="posts",
    )
    status = models.CharField(
        verbose_name="Статус",
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
    )
    post_type = models.CharField(
        verbose_name="Тип",
        max_length=20,
        choices=PostType.choices,
        default=PostType.EDITORIAL,
        help_text="Визначає позначку «Партнерський матеріал» для непередакційного типу.",
    )
    guest_author_name = models.CharField(
        verbose_name="Гостьовий автор",
        max_length=255,
        blank=True,
        help_text="Заповнюється лише для гостьових/спонсорованих публікацій.",
    )
    submitter_contact = models.CharField(
        verbose_name="Контакт автора",
        max_length=255,
        blank=True,
        help_text="Службове поле, не публічне.",
    )
    sources = models.ManyToManyField(
        "patterns.Source",
        verbose_name="Джерела",
        blank=True,
        related_name="blog_posts",
        help_text="Обов'язково для статей з історичними чи символічними твердженнями.",
    )
    related_region = models.ForeignKey(
        "patterns.Region",
        verbose_name="Регіон",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="blog_posts",
        help_text=(
            "Якщо стаття присвячена конкретному регіону - для взаємного "
            "перелінкування (SEO-кластер)."
        ),
    )
    published_at = models.DateTimeField(verbose_name="Дата публікації", null=True, blank=True)
    seo_title = models.CharField(verbose_name="SEO title", max_length=255, blank=True)
    seo_description = models.TextField(verbose_name="SEO description", blank=True)
    target_keyword = models.CharField(
        verbose_name="Ключове слово",
        max_length=255,
        blank=True,
        help_text="Цільове ключове слово/фраза для цієї статті (SEO).",
    )

    slug_source_field = "title_uk"

    def save(self, *args, **kwargs):
        import bleach

        for field in ("body", "body_en"):
            setattr(
                self,
                field,
                bleach.clean(
                    getattr(self, field) or "",
                    tags=settings.ALLOWED_BLOG_HTML_TAGS,
                    attributes=settings.ALLOWED_BLOG_HTML_ATTRIBUTES,
                    strip=True,
                ),
            )
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        from django.urls import reverse

        return reverse("blog:detail", args=[self.slug])

    @property
    def has_english(self):
        return bool((self.body_en or "").strip())

    @property
    def image_urls(self):
        """Обкладинка й фото з тексту статті (обидві мови), без повторів."""
        found = [self.cover_image_url] if self.cover_image_url else []
        for body in (self.body, self.body_en):
            found += re.findall(r'<img[^>]+src="([^"]+)"', body or "")
        return list(dict.fromkeys(found))

    @property
    def localized_body(self):
        if (get_language() or "").startswith("en") and self.has_english:
            return self.body_en
        return self.body

    @property
    def reading_minutes(self):
        words = len(strip_tags(self.localized_body or "").split())
        return max(1, round(words / 200))

    @property
    def breadcrumbs(self):
        from django.urls import reverse

        return [
            {"label": _("Блог"), "url": reverse("blog:list")},
            {
                "label": self.category.name,
                "url": f"{reverse('blog:list')}?category={self.category.slug}",
            },
            {"label": self.title},
        ]

    class Meta:
        verbose_name = "Стаття блогу"
        verbose_name_plural = "Статті блогу"
        ordering = ["-published_at"]

    def __str__(self):
        return self.title


class GuestPostSubmission(TimeStampedModel):
    """Заявка на гостьовий пост."""

    class ReviewStatus(models.TextChoices):
        NEW = "new", "Нова"
        IN_REVIEW = "in_review", "На розгляді"
        APPROVED = "approved", "Схвалено"
        REJECTED = "rejected", "Відхилено"

    class CollaborationType(models.TextChoices):
        GUEST = "guest", gettext_lazy("Гостьова стаття")
        SPONSORED = "sponsored", gettext_lazy("Спонсорський матеріал")
        WRITTEN_BY_US = "written_by_us", gettext_lazy("Текст під ключ (пишемо ми)")
        PARTNERSHIP = "partnership", gettext_lazy("Партнерство")
        SPONSORSHIP = "sponsorship", gettext_lazy("Спонсорство проєкту")
        OTHER = "other", gettext_lazy("Інше")

    contact_name = models.CharField(gettext_lazy("Ваше ім'я"), max_length=255)
    email = models.EmailField(gettext_lazy("Email"))
    brand_name = models.CharField(gettext_lazy("Бренд або організація"), max_length=255, blank=True)
    collaboration_type = models.CharField(
        gettext_lazy("Формат співпраці"),
        max_length=20,
        choices=CollaborationType.choices,
        default=CollaborationType.GUEST,
    )
    proposed_topic = models.CharField(gettext_lazy("Тема або проєкт"), max_length=255)
    proposal_description = models.TextField(gettext_lazy("Коротко про пропозицію"))
    # Приховане поле проти автоматичного спаму - має лишатись порожнім.
    # Без help_text: aria-describedby вказував би на текст, якого немає на сторінці.
    honeypot = models.CharField(max_length=255, blank=True)
    submitter_ip = models.GenericIPAddressField("IP", null=True, blank=True)
    review_status = models.CharField(
        "Статус",
        max_length=20,
        choices=ReviewStatus.choices,
        default=ReviewStatus.NEW,
    )

    class Meta:
        verbose_name = "Заявка на гостьовий пост"
        verbose_name_plural = "Заявки на гостьові пости"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.contact_name} - {self.proposed_topic}"
