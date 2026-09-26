from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("puntenteller", "0020_rijksmonument"),
    ]

    operations = [
        migrations.AddField(
            model_name="kengetal",
            name="monument_beschermd_stads_of_dorpsgezicht_huurprijsopslag_factor",
            field=models.DecimalField(decimal_places=2, default=1.15, max_digits=4),
        ),
        migrations.AddField(
            model_name="kengetal",
            name="monument_gemeentelijk_of_provinciaal_huurprijsopslag_factor",
            field=models.DecimalField(decimal_places=2, default=1.15, max_digits=4),
        ),
    ]
