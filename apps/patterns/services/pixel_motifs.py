"""
Піксельна модель мотивів (пропозиція, кандидат на ADR) — Stage 5, Трек Б.

Формат geometry_parameters (замість base_points + symmetry):

    {
        "format": "pixel_grid_v1",
        "grid": [
            ".....#.....",
            "....#.#....",
            ...
        ],
        "palette": {"#": 0, "o": 1}
    }

- grid — рядки однакової довжини; кожен символ = одна клітинка-стібок,
  "." — порожня клітинка (тло сорочки просвічує).
- palette — символ -> індекс у region.dominant_colors. Мотив не знає
  конкретних кольорів: та сама схема автоматично перефарбовується
  палітрою регіону, як і в реальних друкованих схемах.
- Це прямий відповідник рахункової/сітчастої техніки (хрестик, низь):
  клітинку можна переносити 1:1 з довідкових схем-зображень, не
  реконструюючи криві.

Симетрія сітки — прості трансформації, замість обчислень осі через
max(x): дзеркало = розворот рядків/стовпців. Самоперетин неможливий
за побудовою (рендер — осьові прямокутники), тож клас помилок ADR 5 /
ADR 13 (Self-intersection) зникає як категорія.
"""

GridGeometry = dict

EMPTY = "."


_BODY_COLOR = "#FFFFFF"


def visible_color(color: str) -> str:
    """ЛИШЕ чистий білий (акцент орнаменту, що збігається з тлом сорочки)
    робиться ледь сірим, щоб проглядався. Кольорові та навмисно-сірі
    (Полтавщина #D9D9D9) НЕ чіпаються — точний збіг із тлом, без
    luminance-порогу, який раніше помилково сірив світлі кольори орнаменту."""
    return "#EDEDED" if color.strip().upper() == _BODY_COLOR else color


def build_ornament_palette(region_colors: list[str]) -> list[str]:
    """Провідний білий у палітрі = колір тканини, не орнаменту: прибираємо
    його, щоб мотив (index 0) малювався кольором орнаменту, а не зникав на
    білому тлі. Білі-акценти всередині палітри лишаються (їх робить видимими
    visible_color). Повністю світлі палітри (Полтавщина) не чіпаються."""
    colors = list(region_colors) if region_colors else ["#000000"]
    while len(colors) > 1 and colors[0].strip().upper() == _BODY_COLOR:
        colors = colors[1:]
    return colors


def validate_grid(geometry: GridGeometry) -> None:
    grid = geometry["grid"]
    palette = geometry["palette"]
    if not grid:
        raise ValueError("Порожня сітка мотиву.")
    width = len(grid[0])
    if width == 0:
        raise ValueError("Порожній рядок сітки.")
    for row in grid:
        if len(row) != width:
            raise ValueError("Рядки сітки мають різну довжину.")
        for ch in row:
            if ch != EMPTY and ch not in palette:
                raise ValueError(f"Символ {ch!r} відсутній у palette.")


def mirror_horizontal(grid: list[str]) -> list[str]:
    """Дзеркало відносно вертикальної осі — розворот кожного рядка."""
    return [row[::-1] for row in grid]


def mirror_vertical(grid: list[str]) -> list[str]:
    """Дзеркало відносно горизонтальної осі — розворот порядку рядків."""
    return list(reversed(grid))


def repeat_horizontal(grid: list[str], times: int) -> list[str]:
    """Шпалерне p1-повторення по горизонталі — конкатенація рядків."""
    return [row * times for row in grid]


def render_grid_in_zone(geometry: GridGeometry, zone: dict, colors: list[str]) -> str:
    """
    Замостити зону сіткою мотиву.

    Клітинка квадратна: сторона = коротша сторона зони / к-ть клітинок
    упоперек. Уздовж довшої сторони мотив повторюється цілим числом
    разів (тайл трохи розтягується, щоб заповнити зону без обрізань —
    спотворення в межах одного тайла, не накопичується).

    Горизонтальні прогони клітинок одного кольору зливаються в один
    <rect> — щільний мотив не роздуває SVG (важливо: SVG зберігається
    текстом у базі, розділ 3.5 ТЗ).
    """
    validate_grid(geometry)
    grid, palette = geometry["grid"], geometry["palette"]
    n_rows, n_cols = len(grid), len(grid[0])

    horizontal = zone["width"] >= zone["height"]
    if horizontal:
        cell = zone["height"] / n_rows
        tiles = max(1, round(zone["width"] / (cell * n_cols)))
        tile_w, tile_h = zone["width"] / tiles, zone["height"]
    else:
        cell = zone["width"] / n_cols
        tiles = max(1, round(zone["height"] / (cell * n_rows)))
        tile_w, tile_h = zone["width"], zone["height"] / tiles

    cw, ch = tile_w / n_cols, tile_h / n_rows
    rects = []
    for t in range(tiles):
        ox = zone["x"] + (t * tile_w if horizontal else 0)
        oy = zone["y"] + (0 if horizontal else t * tile_h)
        for r, row in enumerate(grid):
            c = 0
            while c < n_cols:
                ch_sym = row[c]
                if ch_sym == EMPTY:
                    c += 1
                    continue
                run_start = c
                while c < n_cols and row[c] == ch_sym:
                    c += 1
                color = visible_color(colors[palette[ch_sym] % len(colors)])
                rects.append(
                    f'<rect x="{ox + run_start * cw:.2f}" y="{oy + r * ch:.2f}" '
                    f'width="{(c - run_start) * cw:.2f}" height="{ch:.2f}" fill="{color}"/>'
                )
    return "".join(rects)
