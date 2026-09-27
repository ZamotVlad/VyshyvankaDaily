from django.db import migrations

OLD = "authors/vlad.png"
NEW = "authors/vladyslav-zamotailo-author.webp"


def forwards(apps, schema_editor):
    Author = apps.get_model("blog", "Author")
    for author in Author.objects.filter(avatar_url__contains=OLD):
        author.avatar_url = author.avatar_url.replace(OLD, NEW)
        author.save(update_fields=["avatar_url"])


def backwards(apps, schema_editor):
    Author = apps.get_model("blog", "Author")
    for author in Author.objects.filter(avatar_url__contains=NEW):
        author.avatar_url = author.avatar_url.replace(NEW, OLD)
        author.save(update_fields=["avatar_url"])


class Migration(migrations.Migration):
    dependencies = [("blog", "0009_blogpost_cover_image_alt")]

    operations = [migrations.RunPython(forwards, backwards)]
