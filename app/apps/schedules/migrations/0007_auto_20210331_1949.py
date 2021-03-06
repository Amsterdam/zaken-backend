# Generated by Django 3.1.7 on 2021-03-31 17:49

import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("schedules", "0006_auto_20210330_1931"),
    ]

    operations = [
        migrations.AddField(
            model_name="schedule",
            name="date_added",
            field=models.DateTimeField(
                auto_now_add=True, default=django.utils.timezone.now
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="schedule",
            name="date_modified",
            field=models.DateTimeField(auto_now=True),
        ),
    ]
