from django.db import migrations

OLD_UK = (
    "Backend-розробник з України. Самостійно спроєктував і розробив VyshyvankaDaily - платформу, "
    "яка щодня показує орнамент вишиванки одного з 27 регіонів України з реальною історією "
    "символіки з музейних і наукових джерел. Пишу тут про культуру, орнаменти та технічну "
    "сторону проєкту."
)
NEW_UK = (
    "Backend-розробник з України. Сам спроєктував і розробив VyshyvankaDaily: щодня сайт показує "
    "орнамент вишиванки одного з 27 регіонів України з історією його символіки. Факти беру з "
    "музейних колекцій, наукових видань і Національного переліку нематеріальної культурної "
    "спадщини, а джерела наводжу під кожним текстом. Тлумачення символів і перекази подаю з "
    "указанням, хто їх записав. Пишу про вишивку, українську культуру й технічну сторону проєкту."
)
NEW_EN = (
    "Backend developer from Ukraine. I designed and built VyshyvankaDaily on my own: every day "
    "the site shows a vyshyvanka ornament from one of Ukraine's 27 regions, with the history of "
    "its symbolism. I take facts from museum collections, academic publications and Ukraine's "
    "National List of Intangible Cultural Heritage, and list the sources under every text. "
    "Interpretations of symbols and folk accounts are attributed to whoever recorded them. "
    "I write about embroidery, Ukrainian culture and the technical side of the project."
)


def update_bio(apps, schema_editor):
    Author = apps.get_model("blog", "Author")
    # лише якщо в базі ще старий текст, щоб не затерти правки з адмінки
    for author in Author.objects.filter(bio_uk=OLD_UK):
        author.bio = NEW_UK
        author.bio_uk = NEW_UK
        author.bio_en = NEW_EN
        author.save(update_fields=["bio", "bio_uk", "bio_en"])


class Migration(migrations.Migration):
    dependencies = [("blog", "0011_blogpost_body_en")]

    operations = [migrations.RunPython(update_bio, migrations.RunPython.noop)]
