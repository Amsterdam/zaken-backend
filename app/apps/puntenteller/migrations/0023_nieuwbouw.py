from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("puntenteller", "0022_remove_oude_energievelden"),
    ]

    operations = [
        migrations.AddField(
            model_name="gebruikersinvoer",
            name="nieuwbouw",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="kengetal",
            name="nieuwbouw_huurprijsopslag_factor",
            field=models.DecimalField(decimal_places=2, default=1.1, max_digits=4),
        ),
    ]
