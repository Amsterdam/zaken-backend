# Generated by Django 3.0.8 on 2020-07-21 08:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("cases", "0009_auto_20200720_1049"),
    ]

    operations = [
        migrations.AlterField(
            model_name="case",
            name="identification",
            field=models.CharField(blank=True, max_length=255, null=True, unique=True),
        ),
    ]
