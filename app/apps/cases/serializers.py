from apps.cases.models import Address, Case, CaseType
from rest_framework import serializers


class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = "__all__"
        read_only_fields = [
            "id",
            "street_name",
            "number",
            "suffix_letter",
            "suffix",
            "postal_code",
            "lat",
            "lng",
        ]


class CaseTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = CaseType
        fields = "__all__"
        read_only_fields = ["id"]


class CaseSerializer(serializers.ModelSerializer):
    case_type = CaseTypeSerializer(required=True)
    address = AddressSerializer(required=True)

    class Meta:
        model = Case
        fields = "__all__"

    def create(self, validated_data):
        case_type_data = validated_data.pop("case_type")
        case_type = CaseType.get(case_type_data.get("name"))

        address_data = validated_data.pop("address")
        address = Address.get(address_data.get("bag_id"))

        case = Case.objects.create(
            **validated_data, case_type=case_type, address=address
        )

        return case
