import json

from django import template
from django.templatetags.static import static
from django.urls import reverse
from django.utils.html import strip_tags
from django.utils.safestring import mark_safe
from django.utils.translation import gettext as _

register = template.Library()

SITE_NAME = "VyshyvankaDaily"
CONTACT_EMAIL = "vyshyvankadaily@gmail.com"
SAME_AS = ["https://ko-fi.com/vyshyvankadaily"]
PERSON_SOURCE_TYPES = {"academic"}


def _script(data):
    """
    Безпечний вивід JSON-LD. Екранування <, > і & обов'язкове: без нього
    заголовок статті, що містить ці символи, розірве сам тег <script>.
    """
    payload = json.dumps(data, ensure_ascii=False)
    payload = payload.replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
    return mark_safe(f'<script type="application/ld+json">{payload}</script>')


def _home(request):
    return request.build_absolute_uri("/")


def _logo(request):
    return {
        "@type": "ImageObject",
        "url": request.build_absolute_uri(static("favicon/apple-touch-icon.png")),
        "width": 180,
        "height": 180,
    }


def _publisher(request):
    home = _home(request)
    return {
        "@type": "Organization",
        "@id": f"{home}#organization",
        "name": SITE_NAME,
        "url": home,
        "logo": _logo(request),
    }


def _word_count(html):
    return len(strip_tags(html or "").split())


def _citations(sources):
    items = []
    for source in sources:
        entry = {"@type": "CreativeWork", "name": source.name}
        if source.author_or_institution:
            kind = "Person" if source.source_type in PERSON_SOURCE_TYPES else "Organization"
            entry["author"] = {"@type": kind, "name": source.author_or_institution}
        if source.publication_year:
            entry["datePublished"] = str(source.publication_year)
        items.append(entry)
    return items


@register.simple_tag(takes_context=True)
def jsonld_site(context):
    """Organization + WebSite - на кожній сторінці, з base.html."""
    request = context["request"]
    home = _home(request)
    organization = _publisher(request)
    organization["email"] = CONTACT_EMAIL
    organization["sameAs"] = SAME_AS
    data = {
        "@context": "https://schema.org",
        "@graph": [
            organization,
            {
                "@type": "WebSite",
                "@id": f"{home}#website",
                "url": home,
                "name": SITE_NAME,
                "publisher": {"@id": f"{home}#organization"},
                "inLanguage": context.get("LANGUAGE_CODE", "uk"),
            },
        ],
    }
    return _script(data)


@register.simple_tag(takes_context=True)
def jsonld_breadcrumbs(context, breadcrumbs):
    """
    BreadcrumbList із того самого джерела, що й видимі хлібні крихти
    (властивість .breadcrumbs на моделі) - жодного дублювання логіки.
    """
    request = context["request"]
    items = [
        {
            "@type": "ListItem",
            "position": 1,
            "name": _("Головна"),
            "item": request.build_absolute_uri("/"),
        }
    ]
    for i, crumb in enumerate(breadcrumbs or [], start=2):
        entry = {"@type": "ListItem", "position": i, "name": crumb["label"]}
        if crumb.get("url"):
            entry["item"] = request.build_absolute_uri(crumb["url"])
        items.append(entry)

    return _script(
        {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": items}
    )


@register.simple_tag(takes_context=True)
def jsonld_article(context, post):
    """BlogPosting для статті блогу."""
    request = context["request"]
    url = request.build_absolute_uri(request.path)
    data = {
        "@context": "https://schema.org",
        "@type": "BlogPosting",
        "headline": post.title,
        "url": url,
        "mainEntityOfPage": {"@type": "WebPage", "@id": url},
        "inLanguage": context.get("LANGUAGE_CODE", "uk"),
        "publisher": _publisher(request),
    }

    # getattr замість прямого звернення: поля можуть називатись інакше,
    # ніж я пам'ятаю, і тег не повинен через це падати.
    excerpt = getattr(post, "excerpt", None)
    if excerpt:
        data["description"] = str(excerpt)

    words = _word_count(context.get("body") or getattr(post, "body", ""))
    if words:
        data["wordCount"] = words

    published = getattr(post, "published_at", None)
    if published:
        data["datePublished"] = published.isoformat()

    updated = getattr(post, "updated_at", None)
    if updated:
        data["dateModified"] = updated.isoformat()

    image = getattr(post, "cover_image_url", None)
    if image:
        data["image"] = image

    blog_author = getattr(post, "blog_author", None)
    author = getattr(post, "guest_author_name", None) or (blog_author.name if blog_author else None)
    data["author"] = {"@type": "Person" if author else "Organization", "name": author or SITE_NAME}
    if blog_author and not getattr(post, "guest_author_name", None):
        data["author"]["url"] = request.build_absolute_uri(
            reverse("blog:author_detail", args=[blog_author.slug])
        )

    sources = getattr(post, "sources", None)
    if sources is not None:
        citations = _citations(sources.all())
        if citations:
            data["citation"] = citations

    return _script(data)


@register.simple_tag(takes_context=True)
def jsonld_region(context, region):
    """Article для сторінки регіону: текст про вишивку з джерелами як citation."""
    request = context["request"]
    url = request.build_absolute_uri(request.path)
    data = {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": region.seo_title or region.name,
        "url": url,
        "mainEntityOfPage": {"@type": "WebPage", "@id": url},
        "inLanguage": context.get("LANGUAGE_CODE", "uk"),
        "image": request.build_absolute_uri(static("og/fallback.png")),
        "author": {"@type": "Organization", "name": SITE_NAME, "url": _home(request)},
        "publisher": _publisher(request),
        "about": {
            "@type": "Place",
            "name": region.name,
            "containedInPlace": {"@type": "Country", "name": _("Україна")},
        },
    }
    if region.seo_description:
        data["description"] = region.seo_description
    words = _word_count(context.get("body") or region.symbolism_description)
    if words:
        data["wordCount"] = words
    if region.created_at:
        data["datePublished"] = region.created_at.isoformat()
    if region.updated_at:
        data["dateModified"] = region.updated_at.isoformat()
    citations = _citations(region.sources.all())
    if citations:
        data["citation"] = citations
    return _script(data)


@register.simple_tag(takes_context=True)
def jsonld_pattern(context, pattern):
    """ImageObject для згенерованого орнаменту дня (SVG)."""
    request = context["request"]
    region = pattern.region
    date = pattern.date.isoformat()
    data = {
        "@context": "https://schema.org",
        "@type": "ImageObject",
        "name": f"{region.name} - {date}",
        "caption": _("Орнамент дня: %(region)s, %(date)s") % {"region": region.name, "date": date},
        "url": request.build_absolute_uri(request.path),
        "contentUrl": request.build_absolute_uri(reverse("patterns:pattern_svg", args=[date])),
        "encodingFormat": "image/svg+xml",
        "datePublished": date,
        "creator": {"@type": "Organization", "name": SITE_NAME, "url": _home(request)},
        "contentLocation": {"@type": "Place", "name": region.name},
    }
    description = getattr(region, "seo_description", None) or strip_tags(
        getattr(region, "symbolism_description", "") or ""
    )
    if description:
        data["description"] = str(description)[:300]
    return _script(data)
