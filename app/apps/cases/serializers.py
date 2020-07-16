from apps.cases.models import Address, Case, CaseType, State, StateType
from rest_framework import serializers


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
        )
        extra_kwargs = {"bag_id": {"validators": []}}


class CaseTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = CaseType
        fields = "__all__"
        read_only_fields = ("id",)
        extra_kwargs = {"name": {"validators": []}}


class CaseSerializer(serializers.ModelSerializer):
    case_type = CaseTypeSerializer(required=True)
    address = AddressSerializer(required=True)

    class Meta:
        model = Case
        fields = "__all__"

    def update(self, instance, validated_data):
        case_type_data = validated_data.pop("case_type", None)
        address_data = validated_data.pop("address", None)

        if case_type_data:
            case_type = CaseType.get(case_type_data.get("name"))
            instance.case_type = case_type

        if address_data:
            address = Address.get(address_data.get("bag_id"))
            instance.address = address

        for key, value in validated_data.items():
            setattr(instance, key, value)

        instance.save()

        return instance

    def create(self, validated_data):
        case_type_data = validated_data.pop("case_type")
        case_type = CaseType.get(case_type_data.get("name"))

        address_data = validated_data.pop("address")
        address = Address.get(address_data.get("bag_id"))

        case = Case.objects.create(
            **validated_data, case_type=case_type, address=address
        )

        return case


class StateTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = StateType
        fields = "__all__"
        read_only_fields = ("id",)


class StateSerializer(serializers.ModelSerializer):
    state_type = StateTypeSerializer(required=True)
    case = CaseSerializer(required=True)

    class Meta:
        model = State
        fields = "__all__"
        read_only_fields = ("id",)
