# Generated by Django 3.2.7 on 2022-01-18 11:34

import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("cases", "0004_auto_20211213_1712"),
    ]

    operations = [
        migrations.AddField(
            model_name="case",
            name="created",
            field=models.DateTimeField(
                auto_now_add=True, default=django.utils.timezone.now
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="case",
            name="last_updated",
            field=models.DateTimeField(auto_now=True),
        ),
    ]