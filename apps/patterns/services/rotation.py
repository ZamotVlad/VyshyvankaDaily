from datetime import date

from apps.patterns.models import Region

# Точка відліку ротації (розділ 8.3 ТЗ). Зафіксована один раз.
# Зміна цієї дати зсуває весь майбутній календар ротації — не міняти
# після першого продакшн-запуску без окремого ADR.
ROTATION_EPOCH = date(2026, 1, 1)


def get_region_for_date(pattern_date: date) -> Region:
    """
    Круговий вибір регіону дня (розділ 8.3 ТЗ).

    Лише верифіковані й активні регіони (Region.objects.verified()) —
    деактивовані/неверифіковані природно пропускаються, бо не входять
    у список ротації.
    """
    regions = list(Region.objects.verified().order_by("rotation_order"))
    if not regions:
        raise Region.DoesNotExist("Немає жодного верифікованого активного регіону.")

    days_passed = (pattern_date - ROTATION_EPOCH).days
    index = days_passed % len(regions)
    return regions[index]
