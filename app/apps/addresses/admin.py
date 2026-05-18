from apps.addresses.models import Address, District, HousingCorporation
from django.contrib import admin


@admin.action(description="Save addresses and update bag data")
def save_addresses(modeladmin, request, queryset):
    for address in queryset:
        address.update_bag_data_and_save_address()


@admin.register(HousingCorporation)
class HousingCorporationAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "bwv_name",
    )


@admin.register(District)
class DistrictAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
    )


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "bag_id",
        "nummeraanduiding_id",
        "postal_code",
        "street_name",
        "number",
        "suffix_letter",
        "suffix",
        "district",
        "housing_corporation",
    )
    list_editable = ("housing_corporation",)
    list_filter = ("housing_corporation", "district")
    search_fields = ("bag_id", "nummeraanduiding_id", "street_name", "postal_code")
    actions = (save_addresses,)
