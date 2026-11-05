import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("decisions", "0004_decision_active"),
    ]

    operations = [
        migrations.AlterField(
            model_name="decision",
            name="date_added",
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
    ]
