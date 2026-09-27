# Додаткові кольори, підтверджені дослідженням і незалежними публікаціями.
# Лише для показу на сторінці регіону, палітру генератора не змінюють.
from django.db import migrations

ACCENT_COLORS = {
    "vinnytska-oblast": ["#E8B923", "#2E7D32"],
    "khmelnytska-oblast": ["#E8B923", "#2E7D32"],
    "ternopilska-oblast": ["#2E7D32", "#E8B923", "#5B2C83"],
    "poltavska-oblast": ["#D00000", "#6EC6E8"],
    "zakarpatska-oblast": ["#5B2C83", "#2A7F8A"],
}


def seed(apps, schema_editor):
    Region = apps.get_model("patterns", "Region")
    for slug, colors in ACCENT_COLORS.items():
        Region.objects.filter(slug=slug).update(accent_colors=colors)


def unseed(apps, schema_editor):
    Region = apps.get_model("patterns", "Region")
    Region.objects.filter(slug__in=ACCENT_COLORS).update(accent_colors=[])


class Migration(migrations.Migration):
    dependencies = [("patterns", "0028_region_accent_colors")]

    operations = [migrations.RunPython(seed, unseed)]
