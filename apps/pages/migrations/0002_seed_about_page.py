from django.db import migrations

PAGES = [
    {
        "slug": "about",
        "title_uk": "Про нас",
        "title_en": "About Us",
        "body_uk": "<p>Текст сторінки «Про нас» — заповнити реальним контентом.</p>",
        "body_en": "<p>About page content — to be filled in.</p>",
    },
    {
        "slug": "terms-of-use",
        "title_uk": "Умови використання",
        "title_en": "Terms of Use",
        "body_uk": (
            "<p><strong>Це технічна заглушка, не остаточний юридичний текст.</strong> "
            "Перед публічним запуском має бути перевірено й доопрацьовано людиною "
            "(розділ 18.5 ТЗ, чек-лист перед запуском).</p>"
            "<p>Використовуючи VyshyvankaDaily, ви погоджуєтесь з умовами, викладеними тут.</p>"
        ),
        "body_en": (
            "<p><strong>Placeholder text, not a final legal document.</strong> "
            "Must be reviewed before public launch.</p>"
        ),
    },
    {
        "slug": "privacy-policy",
        "title_uk": "Політика конфіденційності",
        "title_en": "Privacy Policy",
        "body_uk": (
            "<p><strong>Це технічна заглушка, не остаточний юридичний текст.</strong></p>"
            "<p>Проєкт збирає мінімальний обсяг персональних даних: електронну адресу "
            "та необов'язкове відображуване ім'я (розділ 13 ТЗ). IP-адреси відправників "
            "контактних форм і заявок на гостьовий пост зберігаються виключно для "
            "боротьби зі зловживаннями, з жодною іншою метою не використовуються.</p>"
        ),
        "body_en": "<p><strong>Placeholder text, not a final legal document.</strong></p>",
    },
]


def create_static_pages(apps, schema_editor):
    StaticPage = apps.get_model("pages", "StaticPage")
    for page in PAGES:
        StaticPage.objects.get_or_create(
            slug=page["slug"],
            defaults={
                "title_uk": page["title_uk"],
                "title_en": page["title_en"],
                "body_uk": page["body_uk"],
                "body_en": page["body_en"],
            },
        )


def remove_static_pages(apps, schema_editor):
    StaticPage = apps.get_model("pages", "StaticPage")
    StaticPage.objects.filter(slug__in=[p["slug"] for p in PAGES]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("pages", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(create_static_pages, remove_static_pages),
    ]