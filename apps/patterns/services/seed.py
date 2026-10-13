import hashlib
import random
from datetime import date


def date_to_seed(pattern_date: date) -> str:
    """Людинозрозумілий seed - ISO-рядок дати."""
    return pattern_date.isoformat()


def get_rng(pattern_date: date) -> random.Random:
    """
    Детермінований генератор псевдовипадкових чисел для дати:
    та сама дата завжди дає той самий числовий початковий стан.
    """
    seed_str = date_to_seed(pattern_date)
    digest = hashlib.sha256(seed_str.encode("utf-8")).hexdigest()
    numeric_seed = int(digest, 16) % (2**32)
    return random.Random(numeric_seed)
