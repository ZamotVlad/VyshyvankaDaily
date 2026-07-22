from django.db import migrations

DESCRIPTION_UK = (
    "Полтавщина найвідоміша унікальною технікою «білим по білому» — "
    "вишивкою білими нитками по білому полотну, де візерунок читається "
    "не через колір, а через гру світла на рельєфі стібків. Це "
    "найскладніша технічно вишивальна традиція України. Білі сорочки "
    "були святковим вбранням і для жінок, і для чоловіків; нитки "
    "традиційно вибілювали на сонці біля річки. Домінує білий колір, "
    "іноді підсилений попелясто-сірим для контрасту гри світла; зрідка "
    "трапляються акценти червоного чи блакитного. Серед поширених "
    "мотивів — «ламане гільце», «деревце», «гарбузове листя» "
    "(рослинна група)."
)


def set_poltava_description(apps, schema_editor):
    Region = apps.get_model("patterns", "Region")
    poltava = Region.objects.filter(slug="poltavska-oblast").first()
    if poltava:
        poltava.symbolism_description_uk = DESCRIPTION_UK


def revert_description(apps, schema_editor):
    Region = apps.get_model("patterns", "Region")
    poltava = Region.objects.filter(slug="poltavska-oblast").first()
    if poltava:
        poltava.symbolism_description_uk = ""
        poltava.save()


def _save(apps, schema_editor):
    Region = apps.get_model("patterns", "Region")
    poltava = Region.objects.filter(slug="poltavska-oblast").first()
    if poltava:
        poltava.symbolism_description_uk = DESCRIPTION_UK
        poltava.save()


class Migration(migrations.Migration):

    dependencies = [
        ("patterns", "0005_verify_all_regions"),
    ]

    operations = [
        migrations.RunPython(_save, revert_description),
    ]