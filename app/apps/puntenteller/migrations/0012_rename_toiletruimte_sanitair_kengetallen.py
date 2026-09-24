from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("puntenteller", "0011_toiletruimte_wastafel_punten"),
    ]

    operations = [
        migrations.RenameField(
            model_name="kengetal",
            old_name="toiletruimte_wastafel_max_punten",
            new_name="sanitair_wastafel_niet_badkamer_max_punten",
        ),
        migrations.RenameField(
            model_name="kengetal",
            old_name="toiletruimte_meerpersoons_wastafel_max_punten",
            new_name="sanitair_meerpersoons_wastafel_niet_badkamer_max_punten",
        ),
    ]
