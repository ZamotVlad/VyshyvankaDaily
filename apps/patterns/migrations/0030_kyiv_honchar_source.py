from django.db import migrations

NAME = "Сорочка жіноча, с. Кодаки, І пол. ХХ ст. (КН-22006): опис, схеми вишивки та крою"


def add_source(apps, schema_editor):
    Source = apps.get_model("patterns", "Source")
    Region = apps.get_model("patterns", "Region")
    source, _ = Source.objects.get_or_create(
        name=NAME,
        defaults={
            "source_type": "museum",
            "author_or_institution": "Музей Івана Гончара",
            "reference": (
                "Режим доступу: https://honchar.org.ua/to-learn/"
                "sorochka-zhinocha-chernivetska-oblast-poch-hh-st-1-1-1-1-1-1-1-1-1-1-1-1-1-1-1-i198"
            ),
            "editor_note": "Етнографічний регіон, крій, техніки й кольори сорочки з Кодаків.",
        },
    )
    region = Region.objects.filter(slug="kyivska-oblast").first()
    if region is not None:
        region.sources.add(source)


def remove_source(apps, schema_editor):
    apps.get_model("patterns", "Source").objects.filter(name=NAME).delete()


class Migration(migrations.Migration):
    dependencies = [("patterns", "0029_seed_accent_colors")]

    operations = [migrations.RunPython(add_source, remove_source)]
