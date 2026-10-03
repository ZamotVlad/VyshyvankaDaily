# Наукові джерела (рівень А) і «Також трапляються» для розширених регіонів (03.10.2026).
# Кольори лише для показу на сторінці, палітру генератора не змінюють.
from django.db import migrations

SOURCES = [
    {
        "name": "Народне вбрання Луганщини: етнічна традиція, ідентифікаційні коди",
        "source_type": "academic",
        "author_or_institution": "Скляр В.",
        "publication_year": 2024,
        "reference": "Українознавство, 2024, № 2 (91), с. 66-79.",
        "editor_note": "Сорочки Старобільщини, Сватівщини, Білокуракинщини; заселення з Полтавщини, Київщини, Чернігівщини.",
        "regions": ["luhanska-oblast"],
    },
    {
        "name": "Підгірські жіночі взористі сорочки",
        "source_type": "academic",
        "author_or_institution": "Никорак О., Куцир Т., Юсипчук Ю., Білий В.",
        "publication_year": 2022,
        "reference": "Народознавчі зошити, 2022, № 6 (168).",
        "editor_note": "Ткані уставки й вишивка сорочок Жидачівщини та Калущини.",
        "regions": ["ivano-frankivska-oblast", "lvivska-oblast"],
    },
    {
        "name": (
            "Мереживо та в'язання у народному вбранні гуцулів Рахівщини "
            "кінця ХІХ - початку ХХІ століття: локальні особливості"
        ),
        "source_type": "academic",
        "author_or_institution": "Козакевич О.",
        "publication_year": 2018,
        "reference": "Народознавчі зошити, 2018, № 5 (143).",
        "editor_note": "Межі Гуцульщини за сучасним історико-етнографічним поділом.",
        "regions": ["ivano-frankivska-oblast"],
    },
    {
        "name": "До питання про мотиви в орнаментиці ткацьких виробів українців Одещини",
        "source_type": "academic",
        "author_or_institution": "Стрельцова А.",
        "publication_year": None,
        "reference": "Наукова стаття, с. 167-173. За зібраннями Одеського історико-краєзнавчого музею, Кодимського музею та ОНУ.",
        "editor_note": "Ромб, хрести, «Дерево Роду», виноград і брокарівські троянди на Одещині.",
        "regions": ["odeska-oblast"],
    },
    {
        "name": "Класифікація конструктивних елементів українських національних сорочок Поділля",
        "source_type": "academic",
        "author_or_institution": "Засорнова І.О., Сельська О.О., Мичко А.А.",
        "publication_year": 2016,
        "reference": "Вісник Хмельницького національного університету, 2016, № 3 (237), с. 272-276.",
        "editor_note": "Крій жіночих сорочок за фондами Хмельницького обласного краєзнавчого музею.",
        "regions": ["khmelnytska-oblast"],
    },
    {
        "name": (
            "Комплексне етнографічне вивчення Північної Житомирщини: здобутки і перспективи "
            "(за матеріалами середини ХІХ - ХХ ст.)"
        ),
        "source_type": "academic",
        "author_or_institution": "Несен І.І.",
        "publication_year": 2017,
        "reference": "Археологія і давня історія України, 2017, вип. 4 (25).",
        "editor_note": "Дослідження поліського костюма, парна запаска, закладні тканини околичної шляхти.",
        "regions": ["zhytomyrska-oblast"],
    },
    {
        "name": "Полтавська традиційна вишивка",
        "source_type": "academic",
        "author_or_institution": "Титаренко В.П.",
        "publication_year": 2019,
        "reference": "Вісник Національної академії керівних кадрів культури і мистецтв, 2019, № 4, с. 60-65.",
        "editor_note": "Групи білої вишивки за Є. Антоновичем, барвники, майстрині Полтавщини.",
        "regions": ["poltavska-oblast"],
    },
    {
        "name": "Унікальний досвід майстринь-вишивальниць Київщини",
        "source_type": "academic",
        "author_or_institution": "Варивончик А.В.",
        "publication_year": None,
        "reference": "Наукова стаття, Київський національний університет культури і мистецтв.",
        "editor_note": "Київське виробничо-художнє об'єднання ім. Т. Г. Шевченка, Г. Цибульова, Н. Гречановська.",
        "regions": ["m-kyiv"],
    },
    {
        "name": "Донецький обласний краєзнавчий музей",
        "source_type": "institution",
        "author_or_institution": "Енциклопедія сучасної України (Т. Ілляшенко)",
        "publication_year": 2008,
        "reference": "Енциклопедія сучасної України. К.: Інститут енциклопедичних досліджень НАН України, 2008.",
        "editor_note": "Етнографічна колекція з Волноваського району, вишиті сорочки першої половини XIX ст.",
        "regions": ["donetska-oblast"],
    },
]

ACCENT_COLORS = {
    "chernihivska-oblast": ["#1C398E", "#6EC6E8"],
    "luhanska-oblast": ["#FFFFFF", "#000000", "#1C398E"],
    "poltavska-oblast": ["#D00000", "#6EC6E8", "#C8913A"],
    "odeska-oblast": ["#5B2C83", "#1C398E"],
}
PREVIOUS_ACCENTS = {"poltavska-oblast": ["#D00000", "#6EC6E8"]}


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
    for slug in ACCENT_COLORS:
        Region.objects.filter(slug=slug).update(accent_colors=PREVIOUS_ACCENTS.get(slug, []))


class Migration(migrations.Migration):
    dependencies = [("patterns", "0035_accent_colors_sumy_donetsk")]

    operations = [migrations.RunPython(forwards, backwards)]
