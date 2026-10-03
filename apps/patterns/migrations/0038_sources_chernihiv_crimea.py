# Збірник експедиції 2018 року для Чернігівщини; орьнек у Національному переліку для Криму (03.10.2026).
from django.db import migrations

CHERNIHIV = {
    "name": "Народна культура Чернігівського району (традиція та сучасний стан побутування)",
    "source_type": "academic",
    "author_or_institution": (
        "Державний науковий центр захисту культурної спадщини від техногенних катастроф"
    ),
    "publication_year": 2019,
    "reference": (
        "Збірник статей; редкол.: О. Ю. Бріцина, О. О. Васянович, К. А. Литвин та ін. "
        "Житомир: Видавець О. О. Євенок, 2019. 256 с. Статті А. Панкової (одяг), "
        "Н. Телегей (ткані рушники), Г. Троценко (декоративне мистецтво)."
    ),
    "editor_note": "Польові матеріали експедиції 2018 року: сорочки, техніки, місцеві назви, рушники.",
}

PERELIK = "Національний перелік елементів нематеріальної культурної спадщини України"
ORNEK = " Орьнек - кримськотатарський орнамент та знання про нього - наказ від 12.02.2018 № 105."
CRIMEA = ["ar-krym", "m-sevastopol"]


def forwards(apps, schema_editor):
    Source = apps.get_model("patterns", "Source")
    Region = apps.get_model("patterns", "Region")
    data = dict(CHERNIHIV)
    source, _ = Source.objects.get_or_create(name=data.pop("name"), defaults=data)
    for region in Region.objects.filter(slug="chernihivska-oblast"):
        region.sources.add(source)

    perelik = Source.objects.filter(name=PERELIK).first()
    if perelik:
        if ORNEK.strip() not in perelik.reference:
            perelik.reference += ORNEK
            perelik.save(update_fields=["reference"])
        for region in Region.objects.filter(slug__in=CRIMEA):
            region.sources.add(perelik)


def backwards(apps, schema_editor):
    Source = apps.get_model("patterns", "Source")
    Region = apps.get_model("patterns", "Region")
    Source.objects.filter(name=CHERNIHIV["name"]).delete()
    perelik = Source.objects.filter(name=PERELIK).first()
    if perelik:
        perelik.reference = perelik.reference.replace(ORNEK, "")
        perelik.save(update_fields=["reference"])
        for region in Region.objects.filter(slug__in=CRIMEA):
            region.sources.remove(perelik)


class Migration(migrations.Migration):
    dependencies = [("patterns", "0037_sources_and_colors_batch3")]

    operations = [migrations.RunPython(forwards, backwards)]
