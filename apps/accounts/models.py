from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy

from apps.core.models import TimeStampedModel


class Profile(TimeStampedModel):
    """Профіль користувача (розділ 3.7 ТЗ) — розширення User через 1:1."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        verbose_name="Користувач",
        on_delete=models.CASCADE,
        related_name="profile",
    )
    display_name = models.CharField(
        verbose_name=gettext_lazy("Ім'я на сайті"),
        max_length=255,
        blank=True,
        help_text=gettext_lazy("Якщо порожнє, показуємо ім'я користувача."),
    )
    default_language = models.CharField(
        verbose_name=gettext_lazy("Мова"),
        max_length=10,
        blank=True,
        choices=settings.LANGUAGES,
        help_text=gettext_lazy("Необов'язково."),
    )

    current_streak = models.PositiveIntegerField(verbose_name="Серія днів", default=0)
    last_active_date = models.DateField(verbose_name="Остання активність", null=True, blank=True)

    class Meta:
        verbose_name = "Профіль"
        verbose_name_plural = "Профілі"

    def __str__(self):
        return self.get_display_name()

    def get_display_name(self) -> str:
        return self.display_name or self.user.get_username()

    @property
    def displayed_streak(self) -> int:
        """Серія обнуляється для показу, якщо пропущено більше одного дня."""
        from datetime import timedelta

        from django.utils import timezone

        yesterday = timezone.localdate() - timedelta(days=1)
        if self.last_active_date and self.last_active_date >= yesterday:
            return self.current_streak
        return 0
