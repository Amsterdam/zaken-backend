# Generated by Django 3.1.8 on 2021-07-12 09:49

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("events", "0019_auto_20210615_1033"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="caseevent",
            options={"ordering": ["date_created"]},
        ),
    ]
