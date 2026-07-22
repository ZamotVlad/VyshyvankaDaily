from django.db import migrations


def create_khmelnytska_motifs(apps, schema_editor):
    Motif = apps.get_model("patterns", "Motif")
    Region = apps.get_model("patterns", "Region")
    Source = apps.get_model("patterns", "Source")

    region = Region.objects.filter(slug="khmelnytska-oblast").first()
    source = Source.objects.filter(
        name__icontains="Подільські вишивки"
    ).first()
    if region is None:
        return

    zigzag, _ = Motif.objects.get_or_create(
        name_uk="Зубчаста лінія",
        defaults={
            "meaning_description_uk": (
                "Сувора геометрична низь — характерна для Поділля техніка "
                "вишивки прямими, скісними, ламаними, зубчастими лініями, "
                "без рослинних елементів."
            ),
            "geometry_parameters": {
                "base_points": [[0, 10], [5, 0], [10, 10]],
                "symmetry": "wallpaper_p1_horizontal",
                "params": {"step": 10, "repeats": 5},
            },
            "verification_status": "verified",
        },
    )
    zigzag.compatible_regions.add(region)
    if source:
        zigzag.sources.add(source)

    diamond, _ = Motif.objects.get_or_create(
        name_uk="Ромб",
        defaults={
            "meaning_description_uk": (
                "Базова геометрична форма строгої сітчастої вишивки, "
                "поширена по всьому Поділлю."
            ),
            "geometry_parameters": {
                "base_points": [[2.5, 0], [0, 2.5], [2.5, 5]],
                "symmetry": "reflection_vertical",
                "params": {},
            },
            "verification_status": "verified",
        },
    )
    diamond.compatible_regions.add(region)
    if source:
        diamond.sources.add(source)


def remove_khmelnytska_motifs(apps, schema_editor):
    Motif = apps.get_model("patterns", "Motif")
    Motif.objects.filter(name_uk__in=["Зубчаста лінія", "Ромб"]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("patterns", "0008_khmelnytska_and_ternopilska_colors"),
    ]

    operations = [
        migrations.RunPython(create_khmelnytska_motifs, remove_khmelnytska_motifs),
    ]