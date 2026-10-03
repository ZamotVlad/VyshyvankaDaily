# Стаття ЕСУ про кримськотатарське декоративно-ужиткове мистецтво для Криму й Севастополя (03.10.2026).
from django.db import migrations

ESU = {
    "name": "Кримськотатарське декоративно-ужиткове мистецтво",
    "source_type": "academic",
    "author_or_institution": "Акчуріна-Муфтієва Н. М., Заатов І. А.",
    "publication_year": 2014,
    "reference": (
        "Енциклопедія Сучасної України. Київ: Інститут енциклопедичних досліджень "
        "НАН України, 2014."
    ),
    "editor_note": "Техніки вишивки, історія ремесел, дослідники й артілі, відродження після 1990-х.",
}
REGIONS = ["ar-krym", "m-sevastopol"]


def forwards(apps, schema_editor):
    Source = apps.get_model("patterns", "Source")
    Region = apps.get_model("patterns", "Region")
    data = dict(ESU)
    source, _ = Source.objects.get_or_create(name=data.pop("name"), defaults=data)
    for region in Region.objects.filter(slug__in=REGIONS):
        region.sources.add(source)


def backwards(apps, schema_editor):
    Source = apps.get_model("patterns", "Source")
    Source.objects.filter(name=ESU["name"]).delete()


class Migration(migrations.Migration):
    dependencies = [("patterns", "0038_sources_chernihiv_crimea")]

    operations = [migrations.RunPython(forwards, backwards)]
