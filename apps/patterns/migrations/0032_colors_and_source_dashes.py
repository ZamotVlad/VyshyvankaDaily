# Кольори за перевіреними джерелами (docs/VYSHYVANKA_SOURCES.md) і дефіс замість тире в джерелах.
# Палітру генератора (dominant_colors) не змінюємо.
from django.db import migrations

KYIV_HIDDEN = ["#3A7D2C", "#5B2C83", "#E8B923", "#1C398E"]
OCHRE = "#C8913A"
ACCENTS = {
    "kyivska-oblast": [OCHRE],
    "m-kyiv": [OCHRE],
    "zaporizka-oblast": ["#E8B923", "#8B5A2B"],
}
TEXT_FIELDS = ("name", "author_or_institution", "reference", "editor_note")


def dash(value):
    return value.replace("—", "-").replace("–", "-") if value else value


def forwards(apps, schema_editor):
    Region = apps.get_model("patterns", "Region")
    Source = apps.get_model("patterns", "Source")
    Region.objects.filter(slug__in=["kyivska-oblast", "m-kyiv"]).update(
        generator_only_colors=KYIV_HIDDEN
    )
    for slug, colors in ACCENTS.items():
        Region.objects.filter(slug=slug).update(accent_colors=colors)
    for source in Source.objects.all():
        for field in TEXT_FIELDS:
            setattr(source, field, dash(getattr(source, field)))
        source.save(update_fields=list(TEXT_FIELDS))


def backwards(apps, schema_editor):
    Region = apps.get_model("patterns", "Region")
    Region.objects.filter(slug__in=["kyivska-oblast", "m-kyiv"]).update(generator_only_colors=[])
    Region.objects.filter(slug__in=ACCENTS).update(accent_colors=[])


class Migration(migrations.Migration):
    dependencies = [("patterns", "0031_region_generator_only_colors")]

    operations = [migrations.RunPython(forwards, backwards)]
