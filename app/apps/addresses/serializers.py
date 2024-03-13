from apps.addresses.models import Address, District, HousingCorporation
from rest_framework import serializers


class HousingCorporationSerializer(serializers.ModelSerializer):
    class Meta:
        model = HousingCorporation
        exclude = ("bwv_name",)


class DistrictSerializer(serializers.ModelSerializer):
    class Meta:
        model = District
        fields = "__all__"


class AddressSerializer(serializers.ModelSerializer):
    district = DistrictSerializer()

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
            "district",
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
            "district",
        )
        extra_kwargs = {"bag_id": {"validators": []}}


class AddressTinySerializer(serializers.ModelSerializer):
    district = DistrictSerializer()
    housing_corporation = HousingCorporationSerializer()

    # bag_id and housing_corporation are needed in /cases for reports datateam
    class Meta:
        model = Address
        fields = (
            "bag_id",
            "street_name",
            "number",
            "suffix_letter",
            "suffix",
            "postal_code",
            "lat",
            "lng",
            "district",
            "housing_corporation",
        )
        read_only_fields = (
            "bag_id",
            "street_name",
            "number",
            "suffix_letter",
            "suffix",
            "postal_code",
            "lat",
            "lng",
            "district",
            "housing_corporation",
        )

# AddressSimplifiedSerializer is used for the cases in Zakenoverzicht with just a few details.
class AddressSimplifiedSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = (
            "street_name",
            "postal_code",
            "number",
            "suffix_letter",
            "suffix",
        )


class ResidentSerializer(serializers.Serializer):
    geboortedatum = serializers.DateTimeField(required=True)
    geslachtsaanduiding = serializers.ChoiceField(choices=("M", "V", "X"))
    geslachtsnaam = serializers.CharField(required=True)
    voorletters = serializers.CharField(required=True)
    voornamen = serializers.CharField(required=True)
    voorvoegsel_geslachtsnaam = serializers.CharField(required=False)
    datum_begin_relatie_verblijfadres = serializers.DateTimeField(required=True)


class ResidentsSerializer(serializers.Serializer):
    _links = serializers.DictField()
    _embedded = serializers.DictField()


class MeldingenSerializer(serializers.Serializer):
    pageNumber = serializers.IntegerField()
    pageSize = serializers.IntegerField()
    totalPages = serializers.IntegerField()
    totalRecords = serializers.IntegerField()
    data = serializers.ListField(child=serializers.DictField())
