# Generated by Django 3.2.7 on 2021-10-05 09:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("workflow", "0027_caseworkflow_parent_workflow"),
    ]

    operations = [
        migrations.AddField(
            model_name="caseworkflow",
            name="completed",
            field=models.BooleanField(default=False),
        ),
    ]
