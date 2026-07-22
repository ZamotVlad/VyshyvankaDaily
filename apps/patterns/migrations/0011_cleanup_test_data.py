from django.db import migrations


def cleanup(apps, schema_editor):
    Motif = apps.get_model("patterns", "Motif")
    Region = apps.get_model("patterns", "Region")
    Source = apps.get_model("patterns", "Source")
    DailyPattern = apps.get_model("patterns", "DailyPattern")

    khmelnytska = Region.objects.filter(slug="khmelnytska-oblast").first()
    real_source = None
    if khmelnytska:
        real_source = khmelnytska.sources.first()

    # 1. Створюємо ЧИСТИЙ, новий "Ромб" для Хмельниччини - перш ніж
    #    чіпати старий тестовий об'єкт з тією самою назвою.
    if khmelnytska:
        new_diamond = Motif.objects.create(
            name_uk="Ромб",
            meaning_description_uk=(
                "Базова геометрична форма строгої сітчастої вишивки, "
                "поширена по всьому Поділлю."
            ),
            geometry_parameters={
                "base_points": [[2.5, 0], [0, 2.5], [2.5, 5]],
                "symmetry": "reflection_vertical",
                "params": {},
            },
            verification_status="verified",
        )
        new_diamond.compatible_regions.add(khmelnytska)
        if real_source:
            new_diamond.sources.add(real_source)

    # 2. Видаляємо старі DailyPattern, прив'язані до тестового регіону
    #    (інакше PROTECT не дасть видалити сам регіон).
    test_region = Region.objects.filter(name_uk="Тестовий регіон").first()
    if test_region:
        DailyPattern.objects.filter(region=test_region).delete()

    # 3. Видаляємо старі тестові мотиви (тепер безпечно - Хмельниччина
    #    вже має власний, новий "Ромб").
    Motif.objects.filter(name_uk__in=["Ромб", "Хвиля"], verification_status="pending").delete()
    # На випадок, якщо старі тестові мотиви мали verification_status
    # verified (з ранніх ручних правок через shell) - приберемо явно
    # за старим m2m-зв'язком з тестовим регіоном, а не покладаємось
    # лише на статус:
    if test_region:
        for motif in Motif.objects.filter(compatible_regions=test_region):
            if motif.name_uk in ["Ромб", "Хвиля"]:
                motif.delete()

    # 4. Видаляємо сам тестовий регіон і тестові джерела.
    if test_region:
        test_region.delete()
    Source.objects.filter(name__in=["Тестове джерело", "Тестове джерело (dev-seed)"]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("patterns", "0010_all_regions_placeholder_motifs"),
    ]

    operations = [
        migrations.RunPython(cleanup, migrations.RunPython.noop),
    ]