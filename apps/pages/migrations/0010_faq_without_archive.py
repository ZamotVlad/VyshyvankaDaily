from django.db import migrations

# Архів прибрано: відповіді FAQ більше на нього не посилаються.
CHANGES = [
    [
        "Чи можна подивитись орнамент за минулу дату?",
        "Так, через архів. Там зберігається кожен згенерований день від самого початку.",
        "Так, за останні 27 днів - повне коло регіонів: стрічка «Останні дні» на головній і кнопки «попередній / наступний» на сторінці орнаменту. Орнаменти, які ви зберегли у свою колекцію, лишаються там назавжди.",
        "Yes, for the last 27 days, a full cycle of regions: use the Recent days strip on the home page and the previous and next buttons on a pattern page. Patterns you save to your collection stay there for good."
    ],
    [
        "Навіщо реєструватися, якщо орнамент дня доступний і без акаунта?",
        "Для перегляду реєстрація не потрібна: орнамент дня, архів і сторінки регіонів відкриті для всіх. Акаунт потрібен лише щоб зберігати улюблені орнаменти у власну колекцію.",
        "Для перегляду реєстрація не потрібна: орнамент дня, сторінки регіонів і блог відкриті для всіх. Акаунт потрібен лише щоб зберігати улюблені орнаменти у власну колекцію.",
        "You don't need to register to browse: the pattern of the day, the region pages and the blog are open to everyone. An account is only needed to save your favourite patterns to your own collection."
    ],
    [
        "Що означає «Пройдено живих днів» у моїй колекції?",
        "Це кількість унікальних регіонів, орнамент яких ви зберегли саме в день його публікації, а не заднім числом з архіву. Обмеження навмисне: механіка заохочує заходити щодня, а не пройти весь архів за один раз.",
        "Це кількість унікальних регіонів, орнамент яких ви зберегли саме в день його публікації, а не пізніше. Обмеження навмисне: механіка заохочує заходити щодня.",
        "It is the number of unique regions whose pattern you saved on the day it was published, not later. The limit is deliberate: the mechanic encourages you to come back every day."
    ]
]


def apply_change(apps, schema_editor):
    FAQItem = apps.get_model("pages", "FAQItem")
    for question, _old, new_uk, new_en in CHANGES:
        FAQItem.objects.filter(question_uk=question).update(
            answer=new_uk, answer_uk=new_uk, answer_en=new_en
        )


def reverse_change(apps, schema_editor):
    FAQItem = apps.get_model("pages", "FAQItem")
    for question, old_uk, _new_uk, _new_en in CHANGES:
        FAQItem.objects.filter(question_uk=question).update(answer=old_uk, answer_uk=old_uk)


class Migration(migrations.Migration):
    dependencies = [("pages", "0009_faqcategory_name_translation")]
    operations = [migrations.RunPython(apply_change, reverse_change)]
