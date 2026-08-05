from django.db import migrations

NEW_ITEMS = [
    (
        "Орнамент дня",
        5,
        "Чому на сайті 27 регіонів, а не 24?",
        "27 - це кількість адміністративних одиниць України: 24 області, Автономна Республіка Крим і два міста з окремим статусом - Київ і Севастополь. Ми йдемо за цим офіційним поділом, а не лише за списком областей.",
    ),
    (
        "Орнамент дня",
        6,
        "Чому Крим і Севастополь показуються окремо від областей?",
        "Тому що це окремі адміністративні одиниці, не області - так само, як Київ. Кримськотатарський орнамент «орьнек», який представляє Крим на сайті, до того ж належить до окремої традиції, відмінної від материкової української вишивки.",
    ),
]

OLD_TOUR_QUESTION = "Що таке «пройдений тур» у моїй колекції?"
NEW_TOUR_QUESTION = "Що означає «Пройдено живих днів» у моїй колекції?"


def apply_changes(apps, schema_editor):
    FAQCategory = apps.get_model("pages", "FAQCategory")
    FAQItem = apps.get_model("pages", "FAQItem")

    for category_name, order, question, answer in NEW_ITEMS:
        category = FAQCategory.objects.get(name=category_name)
        FAQItem.objects.get_or_create(
            category=category,
            question_uk=question,
            defaults={"question": question, "answer": answer, "answer_uk": answer, "order": order},
        )

    FAQItem.objects.filter(question_uk=OLD_TOUR_QUESTION).update(
        question=NEW_TOUR_QUESTION,
        question_uk=NEW_TOUR_QUESTION,
    )


def reverse_changes(apps, schema_editor):
    FAQItem = apps.get_model("pages", "FAQItem")
    FAQItem.objects.filter(
        question_uk__in=[q for _, _, q, _ in NEW_ITEMS]
    ).delete()
    FAQItem.objects.filter(question_uk=NEW_TOUR_QUESTION).update(
        question=OLD_TOUR_QUESTION,
        question_uk=OLD_TOUR_QUESTION,
    )


class Migration(migrations.Migration):

    dependencies = [
        ("pages", "0006_rewrite_faq"),
    ]

    operations = [
        migrations.RunPython(apply_changes, reverse_changes),
    ]