from django.db import migrations

OLD_ANSWER = "Кожен день має власний ключ генерації, який залежить від дати, а не лише від регіону. Тому навіть коли регіон повторюється після повного циклу ротації, того дня з'явиться новий орнамент, а не точна копія попереднього."
NEW_ANSWER = "Кожен день має власний ключ генерації, прив'язаний до дати - він визначає, який саме з дозволених для регіону мотивів з'явиться того дня. Кількість мотивів на регіон різна й постійно поповнюється, тож розмаїття орнаментів того самого регіону з часом лише зростатиме."


def apply_change(apps, schema_editor):
    FAQItem = apps.get_model("pages", "FAQItem")
    FAQItem.objects.filter(answer_uk=OLD_ANSWER).update(answer=NEW_ANSWER, answer_uk=NEW_ANSWER)


def reverse_change(apps, schema_editor):
    FAQItem = apps.get_model("pages", "FAQItem")
    FAQItem.objects.filter(answer_uk=NEW_ANSWER).update(answer=OLD_ANSWER, answer_uk=OLD_ANSWER)


class Migration(migrations.Migration):
    dependencies = [("pages", "0007_faq_additions")]
    operations = [migrations.RunPython(apply_change, reverse_change)]