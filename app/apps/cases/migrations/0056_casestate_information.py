# Generated by Django 3.1.8 on 2021-05-25 13:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("cases", "0055_auto_20210520_1201"),
    ]

    operations = [
        migrations.AddField(
            model_name="casestate",
            name="information",
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
