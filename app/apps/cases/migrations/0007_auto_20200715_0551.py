# Generated by Django 3.0.8 on 2020-07-15 05:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("cases", "0006_auto_20200715_0350"),
    ]

    operations = [
        migrations.AlterField(
            model_name="case",
            name="start_date",
            field=models.DateField(null=True),
        ),
    ]
