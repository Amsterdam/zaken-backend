# Generated by Django 3.2.13 on 2022-07-12 14:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("cases", "0017_remove_case_directing_process"),
    ]

    operations = [
        migrations.AlterField(
            model_name="advertisement",
            name="link",
            field=models.TextField(),
        ),
    ]
