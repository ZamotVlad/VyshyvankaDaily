# Джерела рівня А для Дніпропетровщини, Тернопільщини, Полтавщини, Вінниччини (03.10.2026).
from django.db import migrations

SOURCES = [
    {
        "name": "Українська вишивка ХІХ - початку ХХ ст. на Катеринославщині",
        "source_type": "academic",
        "author_or_institution": "Маріна З.П.",
        "publication_year": 2013,
        "reference": "Історія і культура Придніпров'я: невідомі та маловідомі сторінки, 2013, вип. 10, с. 121-128.",
        "editor_note": "Рушники XVIII-XX ст., техніки за В. Бабенком, петриківська гладь, кольори.",
        "regions": ["dnipropetrovska-oblast"],
    },
    {
        "name": "Національний перелік елементів нематеріальної культурної спадщини України",
        "source_type": "institution",
        "author_or_institution": "Міністерство культури та інформаційної політики України",
        "publication_year": 2023,
        "reference": (
            "Борщівська народна вишивка - наказ від 13.10.2020 № 2182; "
            "вишивка «білим по білому» Решетилівки - наказ від 29.06.2017 № 561; "
            "вишивка жіночої сорочки на Гадяччині - наказ від 12.07.2023 № 380; "
            "клембівська сорочка «з квіткою» - наказ від 13.10.2020 № 2182."
        ),
        "editor_note": "Офіційні елементи нематеріальної спадщини, пов'язані з вишивкою.",
        "regions": ["ternopilska-oblast", "poltavska-oblast", "vinnytska-oblast"],
    },
]

ACCENT_COLORS = {"dnipropetrovska-oblast": ["#6EC6E8", "#E8B923"]}


def forwards(apps, schema_editor):
    Source = apps.get_model("patterns", "Source")
    Region = apps.get_model("patterns", "Region")
    for item in SOURCES:
        data = dict(item)
        slugs = data.pop("regions")
        source, _ = Source.objects.get_or_create(name=data.pop("name"), defaults=data)
        for region in Region.objects.filter(slug__in=slugs):
            region.sources.add(source)
    for slug, colors in ACCENT_COLORS.items():
        Region.objects.filter(slug=slug).update(accent_colors=colors)


def backwards(apps, schema_editor):
    Source = apps.get_model("patterns", "Source")
    Region = apps.get_model("patterns", "Region")
    Source.objects.filter(name__in=[item["name"] for item in SOURCES]).delete()
    Region.objects.filter(slug__in=ACCENT_COLORS).update(accent_colors=[])


class Migration(migrations.Migration):
    dependencies = [("patterns", "0036_sources_and_colors_batch2")]

    operations = [migrations.RunPython(forwards, backwards)]
