# Generated by Django 3.1.2 on 2020-11-02 08:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("events", "0008_auto_20201030_0425"),
    ]

    operations = [
        migrations.AlterField(
            model_name="event",
            name="type",
            field=models.CharField(
                choices=[("DEBRIEFING", "DEBRIEFING"), ("VISIT", "VISIT")],
                max_length=250,
            ),
        ),
    ]
