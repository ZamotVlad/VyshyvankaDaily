import html
import re

from slugify import slugify

H2_RE = re.compile(r"<h2([^>]*)>(.*?)</h2>", re.S | re.I)
ID_RE = re.compile(r'\s+id="[^"]*"', re.I)


def build_toc(body, reserved=()):
    """Додає id до всіх h2 у HTML і повертає (html, [{"id", "title"}]) для змісту."""
    items, used = [], set(reserved)

    def add_id(match):
        title = html.unescape(re.sub(r"<[^>]+>", "", match.group(2))).strip()
        if not title:
            return match.group(0)
        base = slugify(title, max_length=60, word_boundary=True) or "section"
        anchor, n = base, 2
        while anchor in used:
            anchor, n = f"{base}-{n}", n + 1
        used.add(anchor)
        items.append({"id": anchor, "title": title})
        attrs = ID_RE.sub("", match.group(1))
        return f'<h2 id="{anchor}"{attrs}>{match.group(2)}</h2>'

    return H2_RE.sub(add_id, body or ""), items
