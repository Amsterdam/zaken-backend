# Generated by Django 3.1.8 on 2021-06-29 14:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("cases", "0069_auto_20210614_1702"),
    ]

    operations = [
        migrations.AddField(
            model_name="case",
            name="directing_process",
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]