from apps.addresses.models import Address, HousingCorporation
from django.contrib import admin


@admin.register(HousingCorporation)
class HousingCorporationAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "bwv_name",
    )


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "bag_id",
        "postal_code",
        "street_name",
        "number",
        "suffix_letter",
        "suffix",
        "housing_corporation",
    )
    list_editable = ("housing_corporation",)
