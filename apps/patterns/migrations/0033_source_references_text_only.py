# Джерела лише текстом: без адрес сайтів у полі reference.
from django.db import migrations

REFERENCES = {
    "Українська народна вишивка. Західні області УРСР": "К.: Наукова думка, 1988.",
    "Слобожанський код": "Електронний каталог і віртуальна 3D-виставка, за підтримки УКФ.",
    "Народний одяг Середньої Наддніпрянщини кінця ХІХ - початку ХХІ ст.: локальні особливості": (
        "2017."
    ),
    "Орьнек - Репрезентативний список нематеріальної культурної спадщини людства": (
        "Внесено до Репрезентативного списку ЮНЕСКО 16.12.2021. "
        "Національний перелік Мінкультури України, 2018."
    ),
    "Сорочка жіноча, с. Кодаки, І пол. ХХ ст. (КН-22006): опис, схеми вишивки та крою": (
        "Картка експоната з описом, схемами вишивки та крою."
    ),
}


def forwards(apps, schema_editor):
    Source = apps.get_model("patterns", "Source")
    for name, reference in REFERENCES.items():
        Source.objects.filter(name=name).update(reference=reference)


class Migration(migrations.Migration):
    dependencies = [("patterns", "0032_colors_and_source_dashes")]

    operations = [migrations.RunPython(forwards, migrations.RunPython.noop)]
