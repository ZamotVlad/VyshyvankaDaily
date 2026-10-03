# Джерела рівня А й кольори для регіонів, доповнених 03.10.2026.
from django.db import migrations

SOURCES = [
    {
        "name": "Традиційні жіночі сорочки Волині та Західного Полісся кінця XIX-XX століть",
        "source_type": "museum",
        "author_or_institution": "Волинський краєзнавчий музей; упор. Л. Мірошниченко-Гусак, Т. Хомова",
        "publication_year": 2013,
        "reference": "Каталог збірки. Луцьк: Волинські старожитності, 2013.",
        "editor_note": "378 сорочок з усіх районів області: крій, оздоблення, орнамент.",
        "regions": ["volynska-oblast"],
    },
    {
        "name": "Український жіночий одяг Слобожанщини на початку ХХ ст.",
        "source_type": "academic",
        "author_or_institution": "Попова Т.",
        "publication_year": None,
        "reference": "Стаття в науковому журналі Донецького національного університету імені Василя Стуса.",
        "editor_note": "Мережка, мережаний поділ, кольори, вибивання й лиштва.",
        "regions": ["kharkivska-oblast"],
    },
    {
        "name": "Краєзнавство Таврії: народне вбрання Південної України",
        "source_type": "institution",
        "author_or_institution": "Херсонська обласна універсальна наукова бібліотека ім. Олеся Гончара",
        "publication_year": None,
        "reference": "Віртуальний проєкт «Краєзнавство Таврії»: «Святковий жіночий стрій Херсонщини».",
        "editor_note": "Святковий стрій, розміщення вишивки, кольори й квіти степових сорочок.",
        "regions": ["khersonska-oblast"],
    },
    {
        "name": "Вишивка Східного Поділля",
        "source_type": "museum",
        "author_or_institution": "Вінницький обласний краєзнавчий музей",
        "publication_year": None,
        "reference": "Опис колекції та екскурсії «Традиційний одяг Східного Поділля».",
        "editor_note": "Техніки вишивки Східного Поділля, «Сорочкова карта Вінниччини».",
        "regions": ["vinnytska-oblast"],
    },
    {
        "name": "Гуцульська та покутська вишивка",
        "source_type": "museum",
        "author_or_institution": (
            "Національний музей народного мистецтва Гуцульщини та Покуття ім. Й. Кобринського"
        ),
        "publication_year": None,
        "reference": "Стаття на сайті музею.",
        "editor_note": "Матеріали, техніки й мотиви гуцульської та покутської вишивки.",
        "regions": ["ivano-frankivska-oblast"],
    },
    {
        "name": "Буковинські жіночі сорочки. Каталог приватних та музейних творів",
        "source_type": "academic",
        "author_or_institution": "Лозинський Т.",
        "publication_year": 2017,
        "reference": "Львів, 2017. 336 с.",
        "editor_note": "Каталог буковинських жіночих сорочок.",
        "regions": ["chernivetska-oblast"],
    },
    {
        "name": "Окупована спадщина",
        "source_type": "museum",
        "author_or_institution": "Музей Івана Гончара",
        "publication_year": 2025,
        "reference": "Дослідницько-реконструкторський виставковий проєкт.",
        "editor_note": "12 реконструкцій строїв з тимчасово окупованих територій.",
        "regions": ["zaporizka-oblast", "kharkivska-oblast"],
    },
    {
        "name": "Українська вишиванка: виготовлення вишиванок по регіонах (південний регіон)",
        "source_type": "institution",
        "author_or_institution": "Миколаївський обласний центр народної творчості",
        "publication_year": None,
        "reference": "Матеріал на сайті центру.",
        "editor_note": "Крій і кольори сорочок півдня України.",
        "regions": ["mykolaivska-oblast"],
    },
    {
        "name": "Вишивана моя Саражинка",
        "source_type": "museum",
        "author_or_institution": "Одеський історико-краєзнавчий музей",
        "publication_year": 2025,
        "reference": "Виставка 21.08-20.09.2025 спільно з ГО «Краєзнавчий музей «Моя Саражинка»».",
        "editor_note": "Близько 130 вишитих робіт кількох поколінь села Саражинка.",
        "regions": ["odeska-oblast"],
    },
    {
        "name": (
            "Традиційний народний одяг як джерело вивчення та популяризації "
            "культурної спадщини Закарпаття"
        ),
        "source_type": "academic",
        "author_or_institution": "Коцан В. В.",
        "publication_year": 2015,
        "reference": "Historical and Cultural Studies, 2015, т. 2, № 1.",
        "editor_note": "Вишивка як маркер села, рослинний орнамент 1920-х.",
        "regions": ["zakarpatska-oblast"],
    },
    {
        "name": "Оцифрована колекція сорочок Волинського Полісся",
        "source_type": "museum",
        "author_or_institution": "Березнівський краєзнавчий музей",
        "publication_year": None,
        "reference": "34 найдавніші сорочки з музейної колекції.",
        "editor_note": "Типи крою сорочок Березнівщини.",
        "regions": ["rivnenska-oblast"],
    },
    {
        "name": "Колекція вишиванок Середньої Наддніпрянщини",
        "source_type": "museum",
        "author_or_institution": "Черкаський обласний художній музей",
        "publication_year": None,
        "reference": "Понад 100 сорочок кінця XIX - початку XX ст., онлайн-виставка до Дня вишиванки.",
        "editor_note": "Обсяг колекції, тривалість вишивання сорочки.",
        "regions": ["cherkaska-oblast"],
    },
]

ACCENT_COLORS = {
    "khersonska-oblast": ["#E8B923", "#6EC6E8", "#2E7D32", "#D00000"],
    "mykolaivska-oblast": ["#1C398E", "#6EC6E8", "#C8913A", "#2E7D32"],
    "kharkivska-oblast": ["#E8B923", "#C8913A"],
    "kirovohradska-oblast": ["#E8B923"],
}


def forwards(apps, schema_editor):
    Source = apps.get_model("patterns", "Source")
    Region = apps.get_model("patterns", "Region")
    for item in SOURCES:
        data = dict(item)
        slugs = data.pop("regions")
        source, _ = Source.objects.get_or_create(name=data.pop("name"), defaults=data)
        for region in Region.objects.filter(slug__in=slugs):
            region.sources.add(source)
    for slug, colors in ACCENT_COLORS.items():
        Region.objects.filter(slug=slug).update(accent_colors=colors)


def backwards(apps, schema_editor):
    Source = apps.get_model("patterns", "Source")
    Region = apps.get_model("patterns", "Region")
    Source.objects.filter(name__in=[item["name"] for item in SOURCES]).delete()
    Region.objects.filter(slug__in=ACCENT_COLORS).update(accent_colors=[])


class Migration(migrations.Migration):
    dependencies = [("patterns", "0039_source_esu_crimean_tatar_art")]

    operations = [migrations.RunPython(forwards, backwards)]
