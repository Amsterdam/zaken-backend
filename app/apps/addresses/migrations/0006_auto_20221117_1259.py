# Generated by Django 3.2.13 on 2022-11-17 11:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("addresses", "0005_alter_district_options"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="housingcorporation",
            options={"ordering": ["name"]},
        ),
        migrations.AddField(
            model_name="address",
            name="nummeraanduiding_id",
            field=models.CharField(blank=True, max_length=16, null=True),
        ),
    ]