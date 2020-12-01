from apps.addresses.models import Address
from apps.addresses.serializers import AddressSerializer
from apps.cases.models import Case, CaseState, CaseStateType
from rest_framework import serializers


class CaseStateSerializer(serializers.ModelSerializer):
    status_name = serializers.CharField(source="status.name", read_only=True)

    class Meta:
        model = CaseState
        fields = ["id", "case", "status_name", "status", "state_date", "users"]


class CaseSerializer(serializers.ModelSerializer):
    address = AddressSerializer(required=True)
    case_states = CaseStateSerializer(many=True)
    current_state = CaseStateSerializer(
        source="get_current_state", required=False, read_only=True
    )

    class Meta:
        model = Case
        fields = "__all__"

    def update(self, instance, validated_data):
        address_data = validated_data.pop("address", None)
        if address_data:
            address = Address.get(address_data.get("bag_id"))
            instance.address = address

        for key, value in validated_data.items():
            setattr(instance, key, value)

        instance.save()

        return instance

    def create(self, validated_data):
        address_data = validated_data.pop("address")
        address = Address.get(address_data.get("bag_id"))

        case = Case.objects.create(**validated_data, address=address)

        return case


class PushCaseStateSerializer(serializers.Serializer):
    user_emails = serializers.ListField(child=serializers.EmailField(), required=True)
