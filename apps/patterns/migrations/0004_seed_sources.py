from django.db import migrations

# 13 унікальних джерел (VYSHYVANKA_SOURCES_FINAL.md). Рівень 1 (реальність,
# авторитетність, тематична відповідність) підтверджено пошуком для всіх.
# Рівень 2 (дослівна звірка кожного твердження) НЕ виконаний — саме тому
# verification_status регіонів залишається "pending", не змінюється тут.
SOURCES = {
    "kara-vasylieva": {
        "name": "Історія української вишивки",
        "source_type": "academic",
        "author_or_institution": "Кара-Васильєва Т.В.",
        "reference": "К.: Мистецтво, 2008. Національна премія ім. Т.Шевченка, 2012.",
        "publication_year": 2008,
        "editor_note": (
            "Доповнено дисертацією тієї ж авторки \"Розвиток традицій "
            "полтавської народної вишивки\" (1979) — саме полтавська "
            "специфіка розкрита там детальніше."
        ),
    },
    "zakharchuk-chuhai": {
        "name": "Українська народна вишивка. Західні області УРСР",
        "source_type": "academic",
        "author_or_institution": "Захарчук-Чугай Р.В.",
        "reference": (
            "К.: Наукова думка, 1988. "
            "Повний текст: archive.org/stream/vyshyvka1988/vyshyvka1988_djvu.txt"
        ),
        "publication_year": 1988,
        "editor_note": "",
    },
    "lashchuk": {
        "name": "Народне мистецтво Українського Полісся",
        "source_type": "academic",
        "author_or_institution": "Лащук Ю.",
        "reference": "Львів, 1992.",
        "publication_year": 1992,
        "editor_note": "",
    },
    "pylyp": {
        "name": "Художня вишивка українців Закарпаття ХІХ – першої пол. ХХ ст.",
        "source_type": "academic",
        "author_or_institution": "Пилип Р.І.",
        "reference": "Ужгород, 2012, 468 с.",
        "publication_year": 2012,
        "editor_note": "",
    },
    "slobozhanskyi-kod": {
        "name": "Слобожанський код",
        "source_type": "museum",
        "author_or_institution": "ГО КЛІО ХАБ + Харківський історичний музей ім. Сумцова",
        "reference": "slobocode.art/uk-UA. 500 оцифрованих артефактів, за підтримки УКФ.",
        "publication_year": None,
        "editor_note": "Для Донецької області — часткове охоплення, не повне.",
    },
    "klymchyk": {
        "name": "Подільські вишивки кінця ХІХ – початку ХХ ст., зібрані Ю. Сіцинським",
        "source_type": "academic",
        "author_or_institution": "Климчик О.",
        "reference": (
            "// Україна, 1993, №1. Колекція Кам'янець-Подільського "
            "історичного музею-заповідника."
        ),
        "publication_year": 1993,
        "editor_note": "",
    },
    "demianyshyna": {
        "name": "Українська вишивка (історія костюма Північно-Західного Причорномор'я)",
        "source_type": "academic",
        "author_or_institution": "Дем'янишина Л. (упор.)",
        "reference": "",
        "publication_year": None,
        "editor_note": "",
    },
    "kalyta": {
        "name": "Народна побутова вишивка (кінець XVIII – початок ХХІ ст.). Дніпропетровщина: фотоальбом",
        "source_type": "other",
        "author_or_institution": "Калита Х. / Дніпровська обласна наукова бібліотека",
        "reference": "2016.",
        "publication_year": 2016,
        "editor_note": "",
    },
    "zaporizkyi-museum": {
        "name": "Колекція Запорізького краєзнавчого музею",
        "source_type": "museum",
        "author_or_institution": "Запорізький краєзнавчий музей",
        "reference": "З 1990-х рр.",
        "publication_year": None,
        "editor_note": (
            "ЧЕСНО ПОМІРНИЙ рівень довіри — регіон історично не має єдиної "
            "усталеної традиції вишивки, підтверджено кількома незалежними "
            "джерелами, включно з місцевими."
        ),
    },
    "chernihiv-tarnovskoho": {
        "name": "Вишивка Чернігівщини",
        "source_type": "museum",
        "author_or_institution": "Вид-во Родовід / Чернігівський історичний музей ім. Тарновського",
        "reference": "",
        "publication_year": None,
        "editor_note": "",
    },
    "shchybria": {
        "name": "Народний одяг Середньої Наддніпрянщини кінця ХІХ – початку ХХІ ст.: локальні особливості",
        "source_type": "academic",
        "author_or_institution": "Щибря В. / ІМФЕ ім. Рильського НАН України",
        "reference": "chtyvo.org.ua/authors/Schybria_Volodymyr/. 2017.",
        "publication_year": 2017,
        "editor_note": "",
    },
    "ornek-unesco": {
        "name": "Орьнек — Репрезентативний список нематеріальної культурної спадщини людства",
        "source_type": "institution",
        "author_or_institution": "ЮНЕСКО + Мінкультури України",
        "reference": (
            "ich.unesco.org, внесено 16.12.2021. "
            "Національний перелік Мінкультури України, 2018."
        ),
        "publication_year": 2021,
        "editor_note": "Найвищий рівень довіри — офіційне міжнародне визнання. Підтверджено прямим пошуком.",
    },
    "selivachov": {
        "name": "Лексикон української орнаментики",
        "source_type": "academic",
        "author_or_institution": "Селівачов М.Р. / НАН України",
        "reference": "2005/2009.",
        "publication_year": 2009,
        "editor_note": "Резервне загальне джерело, поки не прив'язане до жодного конкретного регіону.",
    },
}

# slug регіону -> список ключів SOURCES
REGION_SOURCES = {
    "poltavska-oblast": ["kara-vasylieva"],
    "volynska-oblast": ["zakharchuk-chuhai"],
    "rivnenska-oblast": ["zakharchuk-chuhai"],
    "lvivska-oblast": ["zakharchuk-chuhai"],
    "ternopilska-oblast": ["zakharchuk-chuhai"],
    "ivano-frankivska-oblast": ["zakharchuk-chuhai"],
    "chernivetska-oblast": ["zakharchuk-chuhai"],
    "zhytomyrska-oblast": ["lashchuk"],
    "zakarpatska-oblast": ["pylyp"],
    "kharkivska-oblast": ["slobozhanskyi-kod"],
    "sumska-oblast": ["slobozhanskyi-kod"],
    "luhanska-oblast": ["slobozhanskyi-kod"],
    "donetska-oblast": ["slobozhanskyi-kod"],
    "vinnytska-oblast": ["klymchyk"],
    "khmelnytska-oblast": ["klymchyk"],
    "mykolaivska-oblast": ["demianyshyna"],
    "odeska-oblast": ["demianyshyna"],
    "khersonska-oblast": ["demianyshyna"],
    "dnipropetrovska-oblast": ["kalyta"],
    "zaporizka-oblast": ["zaporizkyi-museum"],
    "chernihivska-oblast": ["chernihiv-tarnovskoho"],
    "kyivska-oblast": ["shchybria"],
    "cherkaska-oblast": ["shchybria"],
    "kirovohradska-oblast": ["shchybria"],
    "ar-krym": ["ornek-unesco"],
    "m-sevastopol": ["ornek-unesco"],
    "m-kyiv": ["shchybria"],  # успадковує запис Київської області
}


def create_sources_and_link(apps, schema_editor):
    Source = apps.get_model("patterns", "Source")
    Region = apps.get_model("patterns", "Region")

    source_objects = {}
    for key, data in SOURCES.items():
        obj, _ = Source.objects.get_or_create(
            name=data["name"],
            defaults={
                "source_type": data["source_type"],
                "author_or_institution": data["author_or_institution"],
                "reference": data["reference"],
                "publication_year": data["publication_year"],
                "editor_note": data["editor_note"],
            },
        )
        source_objects[key] = obj

    for region_slug, source_keys in REGION_SOURCES.items():
        try:
            region = Region.objects.get(slug=region_slug)
        except Region.DoesNotExist:
            continue
        for key in source_keys:
            region.sources.add(source_objects[key])
        # verification_status НЕ змінюється — залишається "pending"


def remove_sources(apps, schema_editor):
    Source = apps.get_model("patterns", "Source")
    Source.objects.filter(name__in=[s["name"] for s in SOURCES.values()]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("patterns", "0003_seed_27_regions"),
    ]

    operations = [
        migrations.RunPython(create_sources_and_link, remove_sources),
    ]