# Generated by Django 3.0.8 on 2020-08-06 06:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("cases", "0010_auto_20200721_0802"),
    ]

    operations = [
        migrations.AddField(
            model_name="state",
            name="invoice_identification",
            field=models.CharField(blank=True, max_length=255, null=True, unique=True),
        ),
    ]
