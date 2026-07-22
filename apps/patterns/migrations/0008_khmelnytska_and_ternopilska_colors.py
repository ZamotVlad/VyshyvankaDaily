from django.db import migrations


def apply_color_updates(apps, schema_editor):
    Region = apps.get_model("patterns", "Region")

    # Хмельниччина: текст прямо перелічує чотири конкретні кольори
    # вкраплень (червоний/синій/жовтий/зелений) поруч із домінуючим
    # чорним — обрано 2 з 4 названих для представницького набору.
    khmelnytska = Region.objects.filter(slug="khmelnytska-oblast").first()
    if khmelnytska:
        khmelnytska.dominant_colors = ["#000000", "#FF0000", "#1C398E"]
        khmelnytska.save()

    # Тернопільщина: текст каже лише "з кольоровими контурами", без
    # конкретного кольору. Червоний доданий на основі конвергенції
    # кількох слабших джерел (не одна авторитетна праця) — той самий
    # рівень довіри, що й колір Запоріжжя. Доповнення недомовленого,
    # не суперечність сильнішому джерелу (на відміну від відхиленої
    # пропозиції для Херсонщини).
    ternopilska = Region.objects.filter(slug="ternopilska-oblast").first()
    if ternopilska:
        ternopilska.dominant_colors = ["#000000", "#FF0000"]
        ternopilska.save()


def revert_color_updates(apps, schema_editor):
    Region = apps.get_model("patterns", "Region")
    khmelnytska = Region.objects.filter(slug="khmelnytska-oblast").first()
    if khmelnytska:
        khmelnytska.dominant_colors = ["#000000"]
        khmelnytska.save()
    ternopilska = Region.objects.filter(slug="ternopilska-oblast").first()
    if ternopilska:
        ternopilska.dominant_colors = ["#000000"]
        ternopilska.save()


class Migration(migrations.Migration):

    dependencies = [
        ("patterns", "0007_bulk_symbolism_descriptions"),
    ]

    operations = [
        migrations.RunPython(apply_color_updates, revert_color_updates),
    ]