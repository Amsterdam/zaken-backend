# Generated by Django 3.2.13 on 2022-07-12 09:00

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("addresses", "0004_auto_20220628_1437"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="district",
            options={"ordering": ["name"]},
        ),
    ]
