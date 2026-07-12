from collections.abc import Callable

Point = tuple[float, float]
Shape = list[Point]


def reflect_vertical(points: list[Point], params: dict) -> list[Shape]:
    """
    Група відбиття (розділ 8.4 ТЗ). Повертає ОДНУ фігуру (список форм з 1 елементом).

    Конвенція base_points: відкритий шлях від осі симетрії, через зовнішню
    точку(и), назад до осі — перша й остання точка МАЮТЬ лежати на
    вертикальній осі max(x). Приклад ромба: [(2.5, 0), (0, 2.5), (2.5, 5)].
    Перевірено бібліотекою Shapely (ADR 5) — валідний, без самоперетину.
    """
    axis_x = max(p[0] for p in points)
    mirrored = [(2 * axis_x - x, y) for x, y in points]
    combined = points + list(reversed(mirrored[1:-1]))
    return [combined]


def wallpaper_p1_horizontal(points: list[Point], params: dict) -> list[Shape]:
    """
    Найпростіша шпалерна група (p1) — паралельне перенесення по горизонталі
    (розділ 8.4 ТЗ). Повертає СПИСОК окремих копій-фігур, НЕ один
    об'єднаний контур — злиття копій в один <polygon> давало самоперетинний
    полігон (підтверджено Shapely: Ring Self-intersection), бо ламана між
    кінцем однієї копії й початком наступної не є частиною реального
    контуру мотиву.
    """
    step = params.get("step", 20)
    repeats = params.get("repeats", 3)
    shapes: list[Shape] = []
    for i in range(repeats):
        offset = i * step
        shapes.append([(x + offset, y) for x, y in points])
    return shapes


SYMMETRY_REGISTRY: dict[str, Callable[[list[Point], dict], list[Shape]]] = {
    "reflection_vertical": reflect_vertical,
    "wallpaper_p1_horizontal": wallpaper_p1_horizontal,
}


def apply_symmetry(base_points: list[list[float]], symmetry: str, params: dict) -> list[Shape]:
    """Завжди повертає список фігур (навіть якщо фігура одна) — уніфікований контракт."""
    points = [(p[0], p[1]) for p in base_points]
    transform = SYMMETRY_REGISTRY.get(symmetry)
    if transform is None:
        raise ValueError(f"Невідома група симетрії: {symmetry}")
    return transform(points, params)
