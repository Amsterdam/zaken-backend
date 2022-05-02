# Generated by Django 3.2.7 on 2021-12-23 15:01

import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("openzaak", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="notification",
            name="created_at",
            field=models.DateTimeField(
                auto_now_add=True, default=django.utils.timezone.now
            ),
            preserve_default=False,
        ),
    ]