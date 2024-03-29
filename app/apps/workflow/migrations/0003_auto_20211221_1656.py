# Generated by Django 3.2.7 on 2021-12-21 15:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("workflow", "0002_caseworkflow_case_state_type"),
    ]

    operations = [
        migrations.AddField(
            model_name="caseworkflow",
            name="date_modified",
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AddField(
            model_name="caseworkflow",
            name="started",
            field=models.BooleanField(default=False),
        ),
    ]
