from django.db import migrations

# Кольори: там де VYSHYVANKA_RESEARCH.md дає ТОЧНИЙ hex — використано
# дослівно (Полтавщина, Тернопільщина, Хмельниччина, Волинська,
# Дніпропетровська, Донецька, Запорізька, Рівненська — 8 регіонів).
# Для решти ~19 регіонів файл дає лише словесний опис ("поліхромія",
# "чорно-вишневий") — коди тут є ОРІЄНТОВНОЮ інтерпретацією чату за цим
# описом, НЕ прямою цитатою джерела. Потребує уточнення, коли дійде
# черга до академічного дослідження цих регіонів у Треку А.
REGIONS = [
    ("vinnytska-oblast", "Вінницька область", "Vinnytsia Oblast", "Східне Поділля",
     ["#000000", "#7A1020"]),
    ("volynska-oblast", "Волинська область", "Volyn Oblast", "",
     ["#FF0000", "#1C398E", "#000000"]),
    ("dnipropetrovska-oblast", "Дніпропетровська область", "Dnipropetrovsk Oblast", "",
     ["#FF0000", "#000000"]),
    ("donetska-oblast", "Донецька область", "Donetsk Oblast", "",
     ["#FF0000", "#000000", "#FFFFFF"]),
    ("zhytomyrska-oblast", "Житомирська область", "Zhytomyr Oblast", "",
     ["#D00000", "#000000", "#1C398E"]),
    ("zakarpatska-oblast", "Закарпатська область", "Zakarpattia Oblast", "",
     ["#7A1020", "#000000", "#E8B923", "#2E7D32"]),
    ("zaporizka-oblast", "Запорізька область", "Zaporizhzhia Oblast", "",
     ["#FF0000", "#000000"]),
    ("ivano-frankivska-oblast", "Івано-Франківська область", "Ivano-Frankivsk Oblast", "",
     ["#C46210", "#E8B923", "#7A1020"]),
    ("kyivska-oblast", "Київська область", "Kyiv Oblast", "",
     ["#FFFFFF", "#D00000", "#E8B923", "#1C398E", "#000000"]),
    ("kirovohradska-oblast", "Кіровоградська область", "Kirovohrad Oblast", "",
     ["#D00000", "#000000"]),
    ("luhanska-oblast", "Луганська область", "Luhansk Oblast", "",
     ["#D00000", "#6EC6E8"]),
    ("lvivska-oblast", "Львівська область", "Lviv Oblast", "",
     ["#000000", "#D00000", "#E8B923", "#2E7D32", "#1C398E"]),
    ("mykolaivska-oblast", "Миколаївська область", "Mykolaiv Oblast", "",
     ["#D00000", "#000000", "#8A9BA8"]),
    ("odeska-oblast", "Одеська область", "Odesa Oblast", "",
     ["#000000", "#E8B923", "#D00000"]),
    ("poltavska-oblast", "Полтавська область", "Poltava Oblast", "гладь, білим по білому",
     ["#FFFFFF", "#B5B5B5"]),
    ("rivnenska-oblast", "Рівненська область", "Rivne Oblast", "",
     ["#FF0000", "#1C398E", "#000000"]),
    ("sumska-oblast", "Сумська область", "Sumy Oblast", "",
     ["#FFFFFF", "#D00000", "#1C398E", "#E8B923"]),
    ("ternopilska-oblast", "Тернопільська область", "Ternopil Oblast", "Борщівщина",
     ["#000000"]),
    ("kharkivska-oblast", "Харківська область", "Kharkiv Oblast", "",
     ["#000000", "#D00000"]),
    ("khersonska-oblast", "Херсонська область", "Kherson Oblast", "",
     ["#000000", "#FFFFFF"]),
    ("khmelnytska-oblast", "Хмельницька область", "Khmelnytskyi Oblast", "",
     ["#000000"]),
    ("cherkaska-oblast", "Черкаська область", "Cherkasy Oblast", "Суботів",
     ["#FFFFFF", "#D00000", "#000000", "#C9A227", "#7A1020"]),
    ("chernivetska-oblast", "Чернівецька область", "Chernivtsi Oblast", "Буковина",
     ["#000000", "#7A1020", "#C9C227", "#6B8E23"]),
    ("chernihivska-oblast", "Чернігівська область", "Chernihiv Oblast", "",
     ["#FFFFFF", "#D00000", "#000000"]),
    ("ar-krym", "Автономна Республіка Крим", "Autonomous Republic of Crimea", "кримськотатарська",
     ["#C9506B", "#4E8B5C", "#D9A441"]),
    ("m-kyiv", "місто Київ", "Kyiv City", "",
     ["#FFFFFF", "#D00000", "#E8B923", "#1C398E", "#000000"]),
    ("m-sevastopol", "місто Севастополь", "Sevastopol City", "",
     ["#C9506B", "#4E8B5C", "#D9A441"]),
]


def create_regions(apps, schema_editor):
    Region = apps.get_model("patterns", "Region")
    for order, (slug, name_uk, name_en, cut_type, colors) in enumerate(REGIONS, start=1):
        Region.objects.get_or_create(
            slug=slug,
            defaults={
                "name_uk": name_uk,
                "name_en": name_en,
                "symbolism_description_uk": "",
                "symbolism_description_en": "",
                "dominant_colors": colors,
                "shirt_cut_type": cut_type,
                "rotation_order": order,
                "is_active": True,
                "verification_status": "pending",
            },
        )


def remove_regions(apps, schema_editor):
    Region = apps.get_model("patterns", "Region")
    Region.objects.filter(slug__in=[r[0] for r in REGIONS]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("patterns", "0002_dailypattern_savedpattern"),
    ]

    operations = [
        migrations.RunPython(create_regions, remove_regions),
    ]