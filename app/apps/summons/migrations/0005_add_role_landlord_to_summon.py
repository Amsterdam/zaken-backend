# Generated by Django 4.2.14 on 2024-09-09 10:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("summons", "0004_auto_20220217_1131"),
    ]

    operations = [
        migrations.AlterField(
            model_name="summonedperson",
            name="person_role",
            field=models.CharField(
                choices=[
                    ("PERSON_ROLE_OWNER", "PERSON_ROLE_OWNER"),
                    ("PERSON_ROLE_RESIDENT", "PERSON_ROLE_RESIDENT"),
                    ("PERSON_ROLE_MIDDLEMAN", "PERSON_ROLE_MIDDLEMAN"),
                    ("PERSON_ROLE_PLATFORM", "PERSON_ROLE_PLATFORM"),
                    ("PERSON_ROLE_HEIR", "PERSON_ROLE_HEIR"),
                    ("PERSON_ROLE_LANDLORD", "PERSON_ROLE_LANDLORD"),
                ],
                default="PERSON_ROLE_OWNER",
                max_length=255,
            ),
        ),
    ]
