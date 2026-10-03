# Наукові джерела (рівень А) для розширених текстів Сумщини, Черкащини й Рівненщини (03.10.2026).
from django.db import migrations

PONOMAR = "Ареалогічні інтерпретації традиційного вбрання Якова Прилипка в контексті сучасних викликів"

SOURCES = [
    {
        "name": "Історія української вишиванки на Сумщині",
        "source_type": "academic",
        "author_or_institution": "Голосна О.С.",
        "publication_year": 2017,
        "reference": (
            "Освіта, наука та виробництво: розвиток і перспективи. "
            "Матеріали ІІ Всеукраїнської науково-методичної конференції. Суми: СумДУ, 2017."
        ),
        "editor_note": "Понад 70 технік, кольори й техніки за районами Сумщини.",
        "regions": ["sumska-oblast"],
    },
    {
        "name": PONOMAR,
        "source_type": "academic",
        "author_or_institution": "Пономар Л.",
        "publication_year": 2024,
        "reference": "Матеріали до української етнології, 2024, вип. 23 (26), с. 143-153.",
        "editor_note": "Висновки атласу Я. Прилипка про колір вишивки за регіонами.",
        "regions": ["cherkaska-oblast", "sumska-oblast", "rivnenska-oblast"],
    },
    {
        "name": (
            "Народна сорочка українського Полісся ХІХ - середини ХХ ст. "
            "в контексті досліджень традиційного декоративного мистецтва"
        ),
        "source_type": "academic",
        "author_or_institution": "Вахрамєєва Г.І.",
        "publication_year": 2016,
        "reference": "Парадигма пізнання: гуманітарні питання, 2016, № 3 (14).",
        "editor_note": "Історіографія поліської сорочки, дослідники Рівненщини, музейні збірки.",
        "regions": ["rivnenska-oblast"],
    },]


def add_sources(apps, schema_editor):
    Source = apps.get_model("patterns", "Source")
    Region = apps.get_model("patterns", "Region")
    for item in SOURCES:
        data = dict(item)
        slugs = data.pop("regions")
        source, _ = Source.objects.get_or_create(name=data.pop("name"), defaults=data)
        for region in Region.objects.filter(slug__in=slugs):
            region.sources.add(source)


def remove_sources(apps, schema_editor):
    apps.get_model("patterns", "Source").objects.filter(
        name__in=[item["name"] for item in SOURCES]
    ).delete()


class Migration(migrations.Migration):
    dependencies = [("patterns", "0033_source_references_text_only")]

    operations = [migrations.RunPython(add_sources, remove_sources)]
