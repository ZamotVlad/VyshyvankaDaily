# Міграція 0016 — кольори київського виноградного грона.
#
# Після фікса палітри (visible_color + build_ornament_palette у
# pixel_motifs.py) гроно Києва малювалось червоною гілкою + жовтими
# ягодами — бо палітра Київщини починалась з #D00000/#E8B923, а зеленого
# в ній не було зовсім. Виноград має читатись однозначно.
#
# Рішення: додати зелений (#3A7D2C) і фіолетовий (#5B2C83) на ПЕРШІ дві
# позиції орнаменту палітри Київщини й м. Києва (після білого тла). Тоді
# гроно автоматично: гілка ('#' -> index0 -> зелений), ягоди ('o' ->
# index1 -> фіолетовий). Решта кольорів лишається далі в палітрі — інші
# майбутні мотиви цих регіонів їх ще зможуть використати.
#
# dominant_colors — редакційне поле, тож це свідома контентна правка, не
# рендер-хак. Зелений і фіолетовий історично доречні для виноградного
# «брокарівського» орнаменту Київщини.
from django.db import migrations

# Порядок: тло, гілка(зел), ягоди(фіол), потім історичні кольори регіону.
KYIV_GRAPE_PALETTE = ["#FFFFFF", "#3A7D2C", "#5B2C83", "#D00000", "#E8B923", "#1C398E", "#000000"]

# Попередній стан (для зворотного ходу).
KYIV_OLD_PALETTE = ["#FFFFFF", "#D00000", "#E8B923", "#1C398E", "#000000"]

KYIV_SLUGS = ["kyivska-oblast", "m-kyiv"]


def set_grape_colors(apps, schema_editor):
    Region = apps.get_model("patterns", "Region")
    for slug in KYIV_SLUGS:
        region = Region.objects.filter(slug=slug).first()
        if region is not None:
            region.dominant_colors = list(KYIV_GRAPE_PALETTE)
            region.save()


def revert_grape_colors(apps, schema_editor):
    Region = apps.get_model("patterns", "Region")
    for slug in KYIV_SLUGS:
        region = Region.objects.filter(slug=slug).first()
        if region is not None:
            region.dominant_colors = list(KYIV_OLD_PALETTE)
            region.save()


class Migration(migrations.Migration):
    dependencies = [("patterns", "0015_second_review_fixes")]
    operations = [migrations.RunPython(set_grape_colors, revert_grape_colors)]
