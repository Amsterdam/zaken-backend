from django.db import migrations, models

# Former municipality codes of Weesp (0457) and Muiden (0424). BAG ids keep the
# code of the municipality that issued them, also after the merger with Amsterdam.
WEESP_BAG_ID_PREFIXES = ("0457", "0424")
WEESP_POSTAL_CODE_PREFIX = "138"


def get_city(address):
    postal_code = (address.postal_code or "").replace(" ", "")
    if postal_code.startswith(WEESP_POSTAL_CODE_PREFIX) or (
        address.bag_id or ""
    ).startswith(WEESP_BAG_ID_PREFIXES):
        return "Weesp"
    if postal_code:
        return "Amsterdam"
    # Unknown (e.g. new Weesp addresses without postal code issued under 0363).
    # Left empty so Address.save() retrieves the city from the BAG.
    return None


def set_city(apps, schema_editor):
    Address = apps.get_model("addresses", "Address")
    addresses = list(Address.objects.only("id", "bag_id", "postal_code"))
    for address in addresses:
        address.city = get_city(address)
    Address.objects.bulk_update(addresses, ["city"], batch_size=1000)


class Migration(migrations.Migration):

    dependencies = [
        ("addresses", "0007_alter_address_options"),
    ]

    operations = [
        migrations.AddField(
            model_name="address",
            name="city",
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.RunPython(set_city, migrations.RunPython.noop),
    ]
