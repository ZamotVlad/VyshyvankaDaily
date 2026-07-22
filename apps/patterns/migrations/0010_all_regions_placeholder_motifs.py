from django.db import migrations

# Дві тимчасові, вже перевірені (Shapely, Stage 1) форми — geometry_parameters
# буде замінено на автентичну під час реального Треку Б для кожного регіону.
DIAMOND = {"base_points": [[2.5, 0], [0, 2.5], [2.5, 5]], "symmetry": "reflection_vertical", "params": {}}
WAVE = {"base_points": [[0, 0], [5, 5], [10, 0]], "symmetry": "wallpaper_p1_horizontal", "params": {"step": 15, "repeats": 4}}

# slug -> (назва мотиву, опис значення, DIAMOND чи WAVE)
REGION_MOTIFS = {
    "vinnytska-oblast": ("Геометричний квадрат", "Ритмічне чергування кольорів у квадратах, характерне для подільської вишивки.", WAVE),
    "volynska-oblast": ("Зірки і ромби", "Ритмічне повторення геометричних фігур, що вписуються одна в одну — західноволинський прийом.", DIAMOND),
    "dnipropetrovska-oblast": ("Солярний знак", "Геометризовані хрести й солярні (свастичні) знаки — традиційна символіка сонця.", DIAMOND),
    "donetska-oblast": ("Квітковий букет", "Пишні квіти й дерева, вишиті переважно червоним по білому тлі.", WAVE),
    "zhytomyrska-oblast": ("Розетка", "Найпоширеніший мотив Полісся — восьмикутна зірка й ритмічний повтор ламаних ліній.", DIAMOND),
    "zakarpatska-oblast": ("Кривулька", "Найдавніший геометричний зигзаг закарпатської вишивки.", DIAMOND),
    "zaporizka-oblast": ("Коло з розеткою", "Символ сонця — коло з розеткою всередині, характерне для запорізької вишивки.", DIAMOND),
    "ivano-frankivska-oblast": ("Гуцульська лінія", "Геометричні лінії, що з'єднуються в одну широку динамічну лінію.", WAVE),
    "kyivska-oblast": ("Виноградне гроно", "Поширений мотив «брокарівської» вишивки — рослинний орнамент хрестиком.", WAVE),
    "kirovohradska-oblast": ("Вазон", "Реалістичний рослинний мотив — вазон із квітами й листям.", WAVE),
    "luhanska-oblast": ("Рослинно-геометричний узор", "Поліхромний візерунок хрестиком, вишитий грубою ниткою.", DIAMOND),
    "lvivska-oblast": ("Сосонка (яворівка)", "Дрібний елемент яворівської вишивки з навмисно великим негативним простором.", DIAMOND),
    "mykolaivska-oblast": ("Сосонка", "Стилізований рослинний мотив — сосонка, дубове листя, шишки хмелю.", WAVE),
    "odeska-oblast": ("Двоголовий орел", "Символ під впливом молдовської та румунської традицій.", DIAMOND),
    "poltavska-oblast": ("Ламане гільце", "Рослинний мотив білої гладі — умовне спрощення технічно складнішої техніки «білим по білому».", DIAMOND),
    "rivnenska-oblast": ("Простий геометричний візерунок", "Найдавніший монохромний геометричний орнамент Полісся.", DIAMOND),
    "sumska-oblast": ("Птах", "Зображення птаха символізувало мир і духовну чистоту.", WAVE),
    "ternopilska-oblast": ("Калина з пташками", "Улюблений мотив борщівської вишивки — калина між двома пташками.", WAVE),
    "kharkivska-oblast": ("Дерево життя", "Мотив з меандром, що за традицією символізував підземну воду.", DIAMOND),
    "khersonska-oblast": ("Світове дерево", "Головна ідеограма — образ Матері-Землі (за традицією).", DIAMOND),
    "cherkaska-oblast": ("Дрібний геометричний стібок", "Складний геометричний візерунок, характерний для черкаської вишивки.", WAVE),
    "chernivetska-oblast": ("Букет троянд", "Великі букети троянд і птахи — характерно для Кіцманя.", WAVE),
    "chernihivska-oblast": ("Орликовий мотив", "Двоголовий орел, що з часом трансформувався в рослинні елементи (за традицією).", DIAMOND),
    "ar-krym": ("Марам (дерево життя)", "Кримськотатарський символ дерева життя, вигнута гілка «егрі дал».", WAVE),
}


def create_placeholder_motifs(apps, schema_editor):
    Motif = apps.get_model("patterns", "Motif")
    Region = apps.get_model("patterns", "Region")

    created_for_slug = {}

    for slug, (name, meaning, geometry) in REGION_MOTIFS.items():
        region = Region.objects.filter(slug=slug).first()
        if region is None:
            continue

        motif = Motif.objects.create(
            name_uk=name,
            meaning_description_uk=meaning,
            geometry_parameters=geometry,
            verification_status="pending",  # автентична геометрія - ще не зроблена
        )
        motif.compatible_regions.add(region)
        first_source = region.sources.first()
        if first_source:
            motif.sources.add(first_source)
        created_for_slug[slug] = motif

    # м. Київ / м. Севастополь діляться мотивом материнського регіону
    kyiv_motif = created_for_slug.get("kyivska-oblast")
    m_kyiv = Region.objects.filter(slug="m-kyiv").first()
    if kyiv_motif and m_kyiv:
        kyiv_motif.compatible_regions.add(m_kyiv)

    krym_motif = created_for_slug.get("ar-krym")
    m_sevastopol = Region.objects.filter(slug="m-sevastopol").first()
    if krym_motif and m_sevastopol:
        krym_motif.compatible_regions.add(m_sevastopol)


def remove_placeholder_motifs(apps, schema_editor):
    Motif = apps.get_model("patterns", "Motif")
    Motif.objects.filter(name_uk__in=[v[0] for v in REGION_MOTIFS.values()]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("patterns", "0009_khmelnytska_motifs"),
    ]

    operations = [
        migrations.RunPython(create_placeholder_motifs, remove_placeholder_motifs),
    ]