from django.db import migrations


def copy_uk_to_base(apps, schema_editor):
    Region = apps.get_model("patterns", "Region")
    for region in Region.objects.all():
        region.symbolism_description = region.symbolism_description_uk or ""
        region.save()


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("patterns", "0017_region_target_keyword_region_target_keyword_en_and_more"),
    ]

    operations = [
        migrations.RunPython(copy_uk_to_base, noop_reverse),
    ]