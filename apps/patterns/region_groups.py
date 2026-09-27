from django.utils.translation import get_language
from django.utils.translation import gettext_lazy as _

# Короткі назви для карток і стрічок: (uk, en).
SHORT_NAMES = {
    "vinnytska-oblast": ("Вінниччина", "Vinnytsia"),
    "volynska-oblast": ("Волинь", "Volyn"),
    "dnipropetrovska-oblast": ("Дніпропетровщина", "Dnipropetrovsk"),
    "donetska-oblast": ("Донеччина", "Donetsk"),
    "zhytomyrska-oblast": ("Житомирщина", "Zhytomyr"),
    "zakarpatska-oblast": ("Закарпаття", "Zakarpattia"),
    "zaporizka-oblast": ("Запоріжжя", "Zaporizhzhia"),
    "ivano-frankivska-oblast": ("Івано-Франківщина", "Ivano-Frankivsk"),
    "kyivska-oblast": ("Київщина", "Kyiv region"),
    "kirovohradska-oblast": ("Кіровоградщина", "Kirovohrad"),
    "luhanska-oblast": ("Луганщина", "Luhansk"),
    "lvivska-oblast": ("Львівщина", "Lviv"),
    "mykolaivska-oblast": ("Миколаївщина", "Mykolaiv"),
    "odeska-oblast": ("Одещина", "Odesa"),
    "poltavska-oblast": ("Полтавщина", "Poltava"),
    "rivnenska-oblast": ("Рівненщина", "Rivne"),
    "sumska-oblast": ("Сумщина", "Sumy"),
    "ternopilska-oblast": ("Тернопільщина", "Ternopil"),
    "kharkivska-oblast": ("Харківщина", "Kharkiv"),
    "khersonska-oblast": ("Херсонщина", "Kherson"),
    "khmelnytska-oblast": ("Хмельниччина", "Khmelnytskyi"),
    "cherkaska-oblast": ("Черкащина", "Cherkasy"),
    "chernivetska-oblast": ("Чернівеччина", "Chernivtsi"),
    "chernihivska-oblast": ("Чернігівщина", "Chernihiv"),
    "ar-krym": ("Крим", "Crimea"),
    "m-kyiv": ("Київ", "Kyiv city"),
    "m-sevastopol": ("Севастополь", "Sevastopol"),
}

GROUPS = [
    (
        "west",
        _("Захід"),
        [
            "lvivska-oblast",
            "ternopilska-oblast",
            "ivano-frankivska-oblast",
            "zakarpatska-oblast",
            "chernivetska-oblast",
            "volynska-oblast",
            "rivnenska-oblast",
            "khmelnytska-oblast",
        ],
    ),
    (
        "centre",
        _("Центр"),
        [
            "kyivska-oblast",
            "m-kyiv",
            "vinnytska-oblast",
            "cherkaska-oblast",
            "kirovohradska-oblast",
            "poltavska-oblast",
        ],
    ),
    ("north", _("Північ"), ["zhytomyrska-oblast", "chernihivska-oblast", "sumska-oblast"]),
    (
        "east",
        _("Схід"),
        ["kharkivska-oblast", "dnipropetrovska-oblast", "donetska-oblast", "luhanska-oblast"],
    ),
    (
        "south",
        _("Південь"),
        [
            "odeska-oblast",
            "mykolaivska-oblast",
            "khersonska-oblast",
            "zaporizka-oblast",
            "ar-krym",
            "m-sevastopol",
        ],
    ),
]


def short_name(region):
    names = SHORT_NAMES.get(region.slug)
    if not names:
        return region.name
    return names[1] if (get_language() or "uk").startswith("en") else names[0]


def grouped_regions(regions):
    """Регіони за частинами України; невідомі slug - в останню групу, щоб нічого не загубити."""
    by_slug = {r.slug: r for r in regions}
    groups, used = [], set()
    for key, label, slugs in GROUPS:
        items = [by_slug[s] for s in slugs if s in by_slug]
        used.update(r.slug for r in items)
        groups.append({"key": key, "label": label, "regions": items})
    rest = [r for r in regions if r.slug not in used]
    if rest:
        groups[-1]["regions"].extend(rest)
    return [g for g in groups if g["regions"]]
