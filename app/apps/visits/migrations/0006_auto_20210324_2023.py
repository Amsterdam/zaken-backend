# Generated by Django 3.1.7 on 2021-03-24 19:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("visits", "0005_auto_20201202_1544"),
    ]

    operations = [
        migrations.AlterField(
            model_name="visit",
            name="situation",
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
