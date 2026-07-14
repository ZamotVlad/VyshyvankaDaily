from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.accounts.models import Profile


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_profile_on_user_creation(sender, instance, created, raw, **kwargs):
    """
    Автоматичне створення Profile при реєстрації (розділ 3.7 ТЗ).

    Перевірка `raw` обов'язкова — під час завантаження фікстур (loaddata)
    сигнал спрацьовує без бажаного побічного ефекту, що може викликати
    IntegrityError чи дублікати записів.
    """
    if raw:
        return
    if created:
        Profile.objects.get_or_create(user=instance)
