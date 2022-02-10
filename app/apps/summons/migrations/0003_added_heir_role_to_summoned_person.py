# Generated by Django 3.2.7 on 2022-02-07 15:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("summons", "0002_alter_summonedperson_person_role"),
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
                ],
                default="PERSON_ROLE_OWNER",
                max_length=255,
            ),
        ),
    ]