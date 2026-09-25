import hashlib

# Моделі, чий EN-переклад синхронізується через export/load_translations.
TARGETS = {
    "pages.faqcategory": ("name",),
    "pages.faqitem": ("question", "answer"),
    "patterns.motif": ("name", "meaning_description"),
    "blog.author": ("name", "bio"),
}


def digest(value):
    return hashlib.sha256((value or "").encode("utf-8")).hexdigest()[:12]
