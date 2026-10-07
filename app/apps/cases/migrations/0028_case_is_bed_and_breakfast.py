from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("cases", "0027_delete_casedocument"),
    ]

    operations = [
        migrations.AddField(
            model_name="case",
            name="is_bed_and_breakfast",
            field=models.BooleanField(default=False),
        ),
    ]
