"""Генератор вишиванок 2.0: реалістичний хрестик, регіональні мотиви й компонування."""

import random

from .regions import REGIONS, build_shirt
from .render import render_shirt


def render_region(
    slug: str,
    rng: random.Random,
    label: str,
    colors: list[str] | None = None,
    cycle: int = 0,
) -> str:
    """SVG сорочки регіону; варіанти - rng дати, головний мотив - номер кола."""
    return render_shirt(build_shirt(slug, rng, colors, cycle), label)


__all__ = ["REGIONS", "render_region"]
