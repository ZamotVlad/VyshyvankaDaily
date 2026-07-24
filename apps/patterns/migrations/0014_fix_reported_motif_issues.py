"""
Виправлення трьох конкретних проблем, знайдених при особистому перегляді
debug-сторінки (Stage 5, Трек Б):

1. м. Київ / м. Севастополь мали ІДЕНТИЧНИЙ мотив з материнським регіоном
   (той самий об'єкт Motif через compatible_regions, успадкований ще в
   міграції 0010) — тепер окремий запис: та сама сітка, дзеркально
   розвернута (mirror_horizontal), той самий колір/тема, візуально інша
   композиція. Читає геометрію батьківського мотиву програмно на момент
   застосування міграції — не залежить від точних значень сітки, які
   були написані в попередній сесії.

2. Полтавщина: основний символ сітки мотиву рендерився кольором
   region.dominant_colors[0], який дорівнював #FFFFFF — той самий колір,
   що й SHIRT_BODY (розділ "гладь, білим по білому" у VYSHYVANKA_RESEARCH.md,
   ADR 39 явно попереджав що ця родина апроксимується, не рендериться
   точно). Замінено на видимий світло-сірий, щоб силует хоч проглядався.

3. Сумщина ("Птах"): сітка була занадто розрідженою (за словами власника —
   "просто 4 крапки"), форма не розпізнавалась. Перемальовано розпізнаваним
   силуетом птаха (тіло, крила, хвіст).
"""

from django.db import migrations

SUMY_BIRD_GRID = [
    "....#....",
    "...###...",
    "..#.#.#..",
    ".##.#.##.",
    "#########",
    "..##.##..",
    ".#.....#.",
]

POLTAVA_VISIBLE_GRAY = "#D9D9D9"

CITY_VARIANTS = [
    # (материнський регіон, місто, суфікс назви нового мотиву)
    ("kyivska-oblast", "m-kyiv", "варіація для м. Київ"),
    ("ar-krym", "m-sevastopol", "варіація для м. Севастополь"),
]


def mirror_grid_horizontal(grid: list[str]) -> list[str]:
    """Дзеркало відносно вертикальної осі — розворот кожного рядка."""
    return [row[::-1] for row in grid]


def create_city_variant(apps, region_slug, city_slug, name_suffix):
    Region = apps.get_model("patterns", "Region")
    Motif = apps.get_model("patterns", "Motif")

    parent_region = Region.objects.filter(slug=region_slug).first()
    city_region = Region.objects.filter(slug=city_slug).first()
    if parent_region is None or city_region is None:
        return

    parent_motif = parent_region.compatible_motifs.first()
    if parent_motif is None:
        return

    geometry = dict(parent_motif.geometry_parameters)
    if geometry.get("format") == "pixel_grid_v1":
        geometry["grid"] = mirror_grid_horizontal(geometry["grid"])

    new_name = f"{parent_motif.name_uk} ({name_suffix})"
    city_motif, _ = Motif.objects.get_or_create(
        name_uk=new_name,
        defaults={
            "meaning_description_uk": parent_motif.meaning_description_uk,
            "geometry_parameters": geometry,
            "verification_status": "verified",
        },
    )
    city_motif.sources.set(parent_motif.sources.all())

    # Прибрати успадкований зв'язок зі спільним мотивом материнського
    # регіону, лишити тільки власний, відмінний варіант.
    city_region.compatible_motifs.remove(parent_motif)
    city_region.compatible_motifs.add(city_motif)


def fix_poltava_color(apps):
    Region = apps.get_model("patterns", "Region")
    poltava = Region.objects.filter(slug="poltavska-oblast").first()
    if poltava is None:
        return
    colors = list(poltava.dominant_colors or [])
    if colors:
        colors[0] = POLTAVA_VISIBLE_GRAY
    else:
        colors = [POLTAVA_VISIBLE_GRAY]
    poltava.dominant_colors = colors
    poltava.save()


def fix_sumy_bird(apps):
    Motif = apps.get_model("patterns", "Motif")
    Motif.objects.filter(name_uk="Птах").update(
        geometry_parameters={
            "format": "pixel_grid_v1",
            "grid": SUMY_BIRD_GRID,
            "palette": {"#": 0},
        }
    )


def apply_fixes(apps, schema_editor):
    for region_slug, city_slug, suffix in CITY_VARIANTS:
        create_city_variant(apps, region_slug, city_slug, suffix)
    fix_poltava_color(apps)
    fix_sumy_bird(apps)


def revert_fixes(apps, schema_editor):
    Region = apps.get_model("patterns", "Region")
    Motif = apps.get_model("patterns", "Motif")

    for region_slug, city_slug, suffix in CITY_VARIANTS:
        parent_region = Region.objects.filter(slug=region_slug).first()
        city_region = Region.objects.filter(slug=city_slug).first()
        if parent_region is None or city_region is None:
            continue
        parent_motif = parent_region.compatible_motifs.first()
        variant_name_prefix = parent_motif.name_uk if parent_motif else None
        if variant_name_prefix:
            Motif.objects.filter(name_uk=f"{variant_name_prefix} ({suffix})").delete()
        if parent_motif is not None:
            city_region.compatible_motifs.add(parent_motif)

    poltava = Region.objects.filter(slug="poltavska-oblast").first()
    if poltava is not None:
        colors = list(poltava.dominant_colors or [])
        if colors and colors[0] == POLTAVA_VISIBLE_GRAY:
            colors[0] = "#FFFFFF"
        poltava.dominant_colors = colors
        poltava.save()

    # Примітка: відкат "Птаха" до попередньої (розрідженої) сітки
    # свідомо не реалізований — попередній варіант ніхто не хотів
    # зберігати, це виправлення помилки, не оборотне продуктове рішення.


class Migration(migrations.Migration):
    dependencies = [("patterns", "0013_verify_all_motifs")]
    operations = [migrations.RunPython(apply_fixes, revert_fixes)]