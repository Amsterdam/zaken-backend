# Generated by Django 4.2.18 on 2025-04-10 13:48

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0009_scopedtoken"),
    ]

    operations = [
        migrations.DeleteModel(
            name="ScopedToken",
        ),
    ]
