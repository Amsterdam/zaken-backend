# Generated by Django 3.2.5 on 2021-07-30 13:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("cases", "0078_auto_20210719_1903"),
    ]

    operations = [
        migrations.AlterField(
            model_name="case",
            name="end_date",
            field=models.DateField(blank=True, null=True),
        ),
    ]