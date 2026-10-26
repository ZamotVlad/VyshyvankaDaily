def shade(hex_color: str, k: float) -> str:
    """k < 0 - темніше (множення), k > 0 - світліше (до білого)."""
    h = hex_color.lstrip("#")
    rgb = [int(h[i : i + 2], 16) for i in (0, 2, 4)]
    if k < 0:
        rgb = [int(v * (1 + k)) for v in rgb]
    else:
        rgb = [int(v + (255 - v) * k) for v in rgb]
    return "#" + "".join(f"{v:02x}" for v in rgb)
