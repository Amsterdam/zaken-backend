from apps.addresses.models import Address, District, HousingCorporation
from django.contrib import admin


@admin.action(description="Save addresses and update bag data")
def save_addresses(modeladmin, request, queryset):
    for address in queryset:
        address.save()


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
        "postal_code",
        "street_name",
        "number",
        "suffix_letter",
        "suffix",
        "district",
        "housing_corporation",
    )
    list_editable = ("housing_corporation",)
    list_filter = ("housing_corporation",)
    actions = (save_addresses,)
