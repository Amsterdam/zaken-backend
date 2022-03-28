from apps.addresses.models import Address, HousingCorporation
from rest_framework import serializers


class HousingCorporationSerializer(serializers.ModelSerializer):
    class Meta:
        model = HousingCorporation
        exclude = ("bwv_name",)


class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = (
            "bag_id",
            "id",
            "full_address",
            "street_name",
            "number",
            "suffix_letter",
            "suffix",
            "postal_code",
            "lat",
            "lng",
            "full_address",
            "housing_corporation",
        )
        read_only_fields = (
            "id",
            "street_name",
            "number",
            "suffix_letter",
            "suffix",
            "postal_code",
            "lat",
            "lng",
            "full_address",
            "housing_corporation",
        )
        extra_kwargs = {"bag_id": {"validators": []}}


class ResidentSerializer(serializers.Serializer):
    geboortedatum = serializers.DateTimeField(required=True)
    geslachtsaanduiding = serializers.ChoiceField(choices=("M", "V", "X"))
    geslachtsnaam = serializers.CharField(required=True)
    voorletters = serializers.CharField(required=True)
    voornamen = serializers.CharField(required=True)
    voorvoegsel_geslachtsnaam = serializers.CharField(required=False)
    datum_begin_relatie_verblijfadres = serializers.DateTimeField(required=True)


class ResidentsSerializer(serializers.Serializer):
    results = ResidentSerializer(required=True, many=True)
