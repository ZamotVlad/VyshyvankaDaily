from django.db import migrations, models


class Migration(migrations.Migration):
    """Фаза 2 з 2: видаляє колонку view_count, прибрану з моделі у фазі 1."""

    dependencies = [
        ("patterns", "0025_region_symbolism_description_translation"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.AddField(
                    model_name="dailypattern",
                    name="view_count",
                    field=models.PositiveIntegerField(default=0, db_default=0),
                ),
            ],
        ),
        migrations.RemoveField(
            model_name="dailypattern",
            name="view_count",
        ),
    ]
