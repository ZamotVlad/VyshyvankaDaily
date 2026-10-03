# «Також трапляються» за джерелами 03.10.2026 (Голосна - Сумщина, Проселкова - Донеччина).
# Лише показ на сторінці, палітру генератора не змінюють.
from django.db import migrations

ACCENT_COLORS = {
    "sumska-oblast": ["#000000", "#8C8C8C", "#A67B5B"],
    "donetska-oblast": ["#1C398E"],
}


def seed(apps, schema_editor):
    Region = apps.get_model("patterns", "Region")
    for slug, colors in ACCENT_COLORS.items():
        Region.objects.filter(slug=slug).update(accent_colors=colors)


def unseed(apps, schema_editor):
    Region = apps.get_model("patterns", "Region")
    Region.objects.filter(slug__in=ACCENT_COLORS).update(accent_colors=[])


class Migration(migrations.Migration):
    dependencies = [("patterns", "0034_sources_sumy_cherkasy_rivne")]

    operations = [migrations.RunPython(seed, unseed)]
