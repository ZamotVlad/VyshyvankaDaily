from django.db import migrations, models


class Migration(migrations.Migration):
    """Фаза 2 з 2: видаляє колонку view_count, прибрану з моделі у фазі 1."""

    dependencies = [
        ("blog", "0006_remove_view_count"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.AddField(
                    model_name="blogpost",
                    name="view_count",
                    field=models.PositiveIntegerField(default=0, db_default=0),
                ),
            ],
        ),
        migrations.RemoveField(
            model_name="blogpost",
            name="view_count",
        ),
    ]
