# Generated by Django 3.1.8 on 2021-05-25 12:24

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("decisions", "0006_auto_20210520_1201"),
    ]

    operations = [
        migrations.RenameField(
            model_name="decisiontype",
            old_name="team",
            new_name="theme",
        ),
    ]