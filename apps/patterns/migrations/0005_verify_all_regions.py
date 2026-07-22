from django.db import migrations


def verify_regions_and_apply_fixes(apps, schema_editor):
    Region = apps.get_model("patterns", "Region")
    Source = apps.get_model("patterns", "Source")

    # Рішення власника проєкту (18.07.2026, ADR 36): перехід pending -> verified
    # для всіх 27 на основі Рівня 1 (джерела реальні й релевантні), без
    # завершеного Рівня 2 (дослівна звірка) для 25 з 27. Свідомий компроміс,
    # не помилка процесу.
    Region.objects.all().update(verification_status="verified")

    zaporizhzhia = Region.objects.filter(slug="zaporizka-oblast").first()
    if zaporizhzhia:
        zaporizhzhia.dominant_colors = ["#D00000", "#000000"]
        zaporizhzhia.save()

    # Третє джерело для Полтавщини — монографія, присвячена виключно
    # Полтавщині (доречніша за загальну книгу 2008 р.), підтверджена
    # незалежним пошуком (антикварні каталоги, ResearchGate, Енциклопедія
    # Сучасної України, Комітет Шевченківської премії).
    poltava_source, _ = Source.objects.get_or_create(
        name="Полтавська народна вишивка",
        defaults={
            "source_type": "academic",
            "author_or_institution": "Кара-Васильєва Т.В.",
            "reference": "Київ: Наукова думка, 1983. 136 с.",
            "publication_year": 1983,
            "editor_note": (
                "Монографія присвячена виключно Полтавщині, на відміну від "
                "загальної \"Історії української вишивки\" (2008) — три "
                "джерела тієї самої авторки (1979, 1983, 2008) підсилюють "
                "одне одного."
            ),
        },
    )
    poltava = Region.objects.filter(slug="poltavska-oblast").first()
    if poltava:
        poltava.sources.add(poltava_source)


def revert_fixes(apps, schema_editor):
    Region = apps.get_model("patterns", "Region")
    Source = apps.get_model("patterns", "Source")
    Region.objects.all().update(verification_status="pending")
    Source.objects.filter(name="Полтавська народна вишивка").delete()


class Migration(migrations.Migration):

    dependencies = [
        ("patterns", "0004_seed_sources"),
    ]

    operations = [
        migrations.RunPython(verify_regions_and_apply_fixes, revert_fixes),
    ]