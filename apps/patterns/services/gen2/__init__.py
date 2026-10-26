"""Генератор вишиванок 2.0: реалістичний хрестик, регіональні мотиви й компонування."""

import random

from .regions import REGIONS, build_shirt
from .render import render_shirt


def render_region(
    slug: str, rng: random.Random, label: str, colors: list[str] | None = None
) -> str:
    """SVG сорочки регіону; варіанти визначає rng (детермінований за датою)."""
    return render_shirt(build_shirt(slug, rng, colors), label)


__all__ = ["REGIONS", "render_region"]
