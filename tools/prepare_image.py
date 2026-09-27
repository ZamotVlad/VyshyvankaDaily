"""Готує зображення до публікації: WebP до max_kb, ширина до max_width, описова латинська назва.

python tools/prepare_image.py photo.png girl-vyshyvanka-vinnytska-oblast --max-kb 100
"""

import argparse
import re
from pathlib import Path

from PIL import Image
from slugify import slugify

GENERIC = re.compile(r"(image|img|photo|screenshot|generated|gemini|dsc|pxl|untitled|\d{6,})", re.I)


def clean_name(name: str) -> str:
    slug = slugify(name)
    if len(slug.split("-")) < 2 or GENERIC.search(slug):
        example = "girl-vyshyvanka-vinnytska-oblast"
        raise ValueError(f"Назва має бути описовою, напр. {example}: {slug!r}")
    return slug


def prepare_image(input_path, output_name, max_kb=100, max_width=1600) -> Path:
    img = Image.open(input_path).convert("RGB")
    if img.width > max_width:
        img = img.resize((max_width, round(img.height * max_width / img.width)), Image.LANCZOS)
    output = Path(f"{clean_name(output_name)}.webp")
    quality = 85
    while True:
        img.save(output, "WEBP", quality=quality, method=6)
        if output.stat().st_size <= max_kb * 1024 or quality <= 20:
            break
        quality -= 5
    size_kb = output.stat().st_size // 1024
    print(f"{output} - {size_kb} КБ, {img.width}x{img.height}, quality={quality}")
    if size_kb > max_kb:
        print(f"Увага: більше {max_kb} КБ навіть на мінімальній якості - зменште --max-width.")
    return output


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("input")
    parser.add_argument("name", help="описова назва латиницею через дефіси")
    parser.add_argument("--max-kb", type=int, default=100)
    parser.add_argument("--max-width", type=int, default=1600)
    args = parser.parse_args()
    prepare_image(args.input, args.name, args.max_kb, args.max_width)
