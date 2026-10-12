"""HTML текстів сайту -> простий Markdown для llms-full.txt."""

import re
from html import unescape
from html.parser import HTMLParser

_BLOCK = {"p", "li", "h2", "h3", "h4", "td", "th", "figcaption", "blockquote", "tr"}
_PREFIX = {"h2": "### ", "h3": "#### ", "h4": "##### ", "li": "- ", "blockquote": "> "}


class _Markdown(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.out = []
        self.buf = ""
        self.skip = 0
        self.cells = None
        self.first_row = False

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style"):
            self.skip += 1
        elif tag == "table":
            self.first_row = True
        elif tag == "tr":
            self.cells = []
        elif tag in _BLOCK:
            self.buf = ""
        elif tag == "img":
            alt = dict(attrs).get("alt")
            if alt:
                self.out.append(f"[Зображення: {alt}]")
        elif tag == "br":
            self.buf += " "

    def handle_endtag(self, tag):
        if tag in ("script", "style"):
            self.skip -= 1
            return
        text = " ".join(self.buf.split())
        if tag in ("td", "th") and self.cells is not None:
            self.cells.append(text)
            self.buf = ""
        elif tag == "tr" and self.cells is not None:
            if any(self.cells):
                self.out.append("| " + " | ".join(self.cells) + " |")
                if self.first_row:
                    self.out.append("|" + " --- |" * len(self.cells))
                    self.first_row = False
            self.cells = None
        elif tag in _BLOCK and text:
            self.out.append(_PREFIX.get(tag, "") + text)
            self.buf = ""

    def handle_data(self, data):
        if not self.skip:
            self.buf += data


def html_to_markdown(html):
    parser = _Markdown()
    parser.feed(html or "")
    parser.close()
    lines = []
    for line in parser.out:
        if lines and not (line.startswith("|") and lines[-1].startswith("|")):
            lines.append("")
        lines.append(line)
    text = "\n".join(lines)
    return re.sub(r"\n{3,}", "\n\n", unescape(text)).strip()
