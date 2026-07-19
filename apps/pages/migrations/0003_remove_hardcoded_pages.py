from django.db import migrations

REMOVED_SLUGS = ["about", "terms-of-use", "privacy-policy"]


def remove_pages(apps, schema_editor):
    StaticPage = apps.get_model("pages", "StaticPage")
    StaticPage.objects.filter(slug__in=REMOVED_SLUGS).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("pages", "0002_seed_about_page"),
    ]

    operations = [
        migrations.RunPython(remove_pages, migrations.RunPython.noop),
    ]