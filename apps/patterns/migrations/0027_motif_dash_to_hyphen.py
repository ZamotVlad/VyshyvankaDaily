from django.db import migrations
from django.db.models import Value
from django.db.models.functions import Replace

FIELDS = ("name", "name_uk", "meaning_description", "meaning_description_uk")


def dash_to_hyphen(apps, schema_editor):
    Motif = apps.get_model("patterns", "Motif")
    Motif.objects.update(**{f: Replace(f, Value(" — "), Value(" - ")) for f in FIELDS})


class Migration(migrations.Migration):
    dependencies = [
        ("patterns", "0026_drop_view_count_column"),
    ]

    operations = [
        migrations.RunPython(dash_to_hyphen, migrations.RunPython.noop),
    ]
