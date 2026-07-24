# apps/patterns/migrations/0013_verify_all_motifs.py
from django.db import migrations


def verify_all_motifs(apps, schema_editor):
    Motif = apps.get_model("patterns", "Motif")
    Motif.objects.filter(verification_status="pending").update(
        verification_status="verified"
    )


def revert_to_pending(apps, schema_editor):
    Motif = apps.get_model("patterns", "Motif")
    # Хмельниччина (0009) лишається verified — не займаємо її при відкоті
    Motif.objects.exclude(name_uk__in=["Ромб із засіяним полем", "Зубчаста лінія"]).update(
        verification_status="pending"
    )


class Migration(migrations.Migration):
    dependencies = [("patterns", "0012_all_regions_pixel_geometry")]
    operations = [migrations.RunPython(verify_all_motifs, revert_to_pending)]