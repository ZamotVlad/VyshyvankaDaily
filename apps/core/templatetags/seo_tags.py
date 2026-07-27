import json

from django import template
from django.utils.safestring import mark_safe

register = template.Library()

SITE_NAME = "VyshyvankaDaily"


def _script(data):
    """
    Безпечний вивід JSON-LD. Екранування <, > і & обов'язкове: без нього
    заголовок статті, що містить ці символи, розірве сам тег <script>.
    """
    payload = json.dumps(data, ensure_ascii=False)
    payload = payload.replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")
    return mark_safe(f'<script type="application/ld+json">{payload}</script>')


@register.simple_tag(takes_context=True)
def jsonld_site(context):
    """Organization + WebSite - на кожній сторінці, з base.html."""
    request = context["request"]
    home = request.build_absolute_uri("/")
    data = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "Organization",
                "@id": f"{home}#organization",
                "name": SITE_NAME,
                "url": home,
            },
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
            "name": "Головна",
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
    home = request.build_absolute_uri("/")
    data = {
        "@context": "https://schema.org",
        "@type": "BlogPosting",
        "headline": post.title,
        "url": request.build_absolute_uri(request.path),
        "publisher": {"@type": "Organization", "name": SITE_NAME, "url": home},
    }

    # getattr замість прямого звернення: поля можуть називатись інакше,
    # ніж я пам'ятаю, і тег не повинен через це падати.
    excerpt = getattr(post, "excerpt", None)
    if excerpt:
        data["description"] = str(excerpt)

    published = getattr(post, "published_at", None)
    if published:
        data["datePublished"] = published.isoformat()

    updated = getattr(post, "updated_at", None)
    if updated:
        data["dateModified"] = updated.isoformat()

    image = getattr(post, "cover_image_url", None)
    if image:
        data["image"] = image

    author = getattr(post, "guest_author_name", None)
    data["author"] = {"@type": "Person" if author else "Organization", "name": author or SITE_NAME}

    return _script(data)


@register.simple_tag(takes_context=True)
def jsonld_pattern(context, pattern):
    """VisualArtwork для згенерованого орнаменту дня."""
    request = context["request"]
    region = pattern.region
    data = {
        "@context": "https://schema.org",
        "@type": "VisualArtwork",
        "name": f"{region.name} - {pattern.date.isoformat()}",
        "url": request.build_absolute_uri(request.path),
        "dateCreated": pattern.date.isoformat(),
        "artform": "Embroidery pattern",
        "creator": {"@type": "Organization", "name": SITE_NAME},
        "locationCreated": {"@type": "Place", "name": region.name},
    }
    description = getattr(region, "symbolism_description", None)
    if description:
        data["description"] = str(description)[:300]
    return _script(data)


@register.simple_tag
def jsonld_faq(categories):
    """
    FAQPage. Чесне застереження: з 2023 року Google показує FAQ-збагачені
    результати лише для авторитетних урядових і медичних сайтів, тож
    видимого рich-сніпета це нам не дасть. Розмітка все одно корисна для
    машинного розуміння структури сторінки, але без завищених очікувань.
    """
    entities = []
    for category in categories or []:
        for item in category.items.all():
            entities.append(
                {
                    "@type": "Question",
                    "name": item.question,
                    "acceptedAnswer": {"@type": "Answer", "text": item.answer},
                }
            )
    if not entities:
        return ""
    return _script({"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": entities})
