# Generated by Django 3.1.8 on 2021-07-12 09:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("cases", "0074_merge_20210712_1132"),
    ]

    operations = [
        migrations.AlterField(
            model_name="caseproject",
            name="name",
            field=models.CharField(max_length=255),
        ),
    ]
