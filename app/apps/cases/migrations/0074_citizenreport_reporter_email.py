# Generated by Django 3.1.8 on 2021-07-13 12:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("cases", "0073_merge_20210701_1104"),
    ]

    operations = [
        migrations.AddField(
            model_name="citizenreport",
            name="reporter_email",
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
    ]