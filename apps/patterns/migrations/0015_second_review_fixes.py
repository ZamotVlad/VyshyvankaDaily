# Міграція 0015 — доопрацювання після другого перегляду debug-сторінки.
#
# Три зауваження власника до результату 0014:
#
# 1. Київщина ("Виноградне гроно") читалось як серце (трикутник ягід
#    з округлим верхом у червоному кольорі). Перемальовано впізнаваним
#    виноградним гроном: вусик-завиток і листя вгорі, щільний трикутник
#    ягід донизу. Ягоди ('o') і гілка ('#') — різні індекси палітри,
#    щоб гроно не зливалось у суцільну пляму.
#    Це також лікує проблему міст (див. нижче): київський мотив тепер
#    сам по собі несиметричний і виразний.
#
# 2. Сумщина ("Птах") — жоден суцільний силует не читався як птах у
#    дрібному масштабі планки. Рішення власника: традиційний прийом —
#    низка пташок-"галочок" у шаховому порядку (ліва, потім права трохи
#    нижче). Кожна пташка — розмах крил + тіло; повторюється вздовж зони.
#
# 3. Міста (Київ/Севастополь) у 0014 дзеркалились по горизонталі, що для
#    їхніх мотивів майже непомітно. Лишаємо підхід 0014 (горизонтальне
#    дзеркало), АЛЕ від оновленого київського грона воно тепер помітне
#    (гроно несиметричне). Для Севастополя (марам) додатково повертаємо
#    на 180 — вигнута гілка стає помітно іншою.
#
# Полтавщину (#D9D9D9) 0014 виправила коректно — не чіпаємо.
from django.db import migrations

KYIV_GRONO_GRID = {
    "format": "pixel_grid_v1",
    "grid": [
        "....#.#....",
        ".##..#..##.",
        "..#.###.#..",
        "....#.#....",
        "...ooooo...",
        "...ooooo...",
        "....ooo....",
        "....ooo....",
        ".....o.....",
        ".....o.....",
    ],
    "palette": {"#": 0, "o": 1},
}

SUMY_BIRDS_GRID = {
    "format": "pixel_grid_v1",
    "grid": [
        "##.##......",
        ".###.......",
        "..#........",
        "......##.##",
        ".......###.",
        "........#..",
    ],
    "palette": {"#": 0},
}


def _vflip(grid):
    """Розворот по вертикалі — гроно перевертається вусиком донизу."""
    return list(reversed(grid))


def _rotate_180(grid):
    return [row[::-1] for row in reversed(grid)]


def apply_fixes(apps, schema_editor):
    Region = apps.get_model("patterns", "Region")
    Motif = apps.get_model("patterns", "Motif")

    # 1. Київське гроно (материнський мотив Київщини + м. Київ через нього).
    Motif.objects.filter(name_uk="Виноградне гроно").update(geometry_parameters=KYIV_GRONO_GRID)

    # 2. Сумські птахи-галочки.
    Motif.objects.filter(name_uk="Птах").update(geometry_parameters=SUMY_BIRDS_GRID)

    # 3. Оновити геометрію міських варіантів від свіжих материнських сіток.
    #    Київ — розворот грона по вертикалі (горизонтальне дзеркало не works:
    #    гроно вертикально-симетричне; vflip дає 29% різниці).
    #    Севастополь — поворот 180 мараму (сильніша різниця для вигнутої гілки).
    for city_slug, transform in [("m-kyiv", _vflip), ("m-sevastopol", _rotate_180)]:
        city = Region.objects.filter(slug=city_slug).first()
        if city is None:
            continue
        city_motif = city.compatible_motifs.filter(name_uk__contains="(варіація").first()
        if city_motif is None:
            continue
        base_name = city_motif.name_uk.split(" (")[0]
        parent = Motif.objects.filter(name_uk=base_name).first()
        if parent is None or parent.geometry_parameters.get("format") != "pixel_grid_v1":
            continue
        geometry = dict(parent.geometry_parameters)
        geometry["grid"] = transform(list(geometry["grid"]))
        city_motif.geometry_parameters = geometry
        city_motif.save()


def revert_fixes(apps, schema_editor):
    """Гроно й птахи назад не відкочуються (виправлення нечитабельних форм,
    той самий принцип, що прийнято в 0014). Міські варіанти лишаються як є."""
    pass


class Migration(migrations.Migration):
    dependencies = [("patterns", "0014_fix_reported_motif_issues")]
    operations = [migrations.RunPython(apply_fixes, revert_fixes)]
