from django.conf import settings
from django.db import models

from apps.core.models import TimeStampedModel


class Profile(TimeStampedModel):
    """Профіль користувача (розділ 3.7 ТЗ) — розширення User через 1:1."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
    )
    display_name = models.CharField(
        max_length=255,
        blank=True,
        help_text="Порожнє значення означає використання імені користувача за замовчуванням.",
    )
    default_language = models.CharField(
        max_length=10,
        blank=True,
        choices=settings.LANGUAGES,
        help_text="Дублює вибір, збережений у сесії/cookie (необов'язково).",
    )

    class Meta:
        verbose_name = "Профіль"
        verbose_name_plural = "Профілі"

    def __str__(self):
        return self.get_display_name()

    def get_display_name(self) -> str:
        return self.display_name or self.user.get_username()
