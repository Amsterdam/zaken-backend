from datetime import datetime

from apps.addresses.models import Address
from apps.addresses.serializers import AddressSerializer
from apps.cases.const import PLAN_VISIT
from apps.cases.models import Case, CaseReason, CaseState, CaseStateType, CaseTeam
from rest_framework import serializers


class CaseTeamSerializer(serializers.ModelSerializer):
    class Meta:
        model = CaseTeam
        fields = "__all__"


class CaseReasonSerializer(serializers.ModelSerializer):
    class Meta:
        model = CaseReason
        fields = "__all__"


class CaseStateSerializer(serializers.ModelSerializer):
    status_name = serializers.CharField(source="status.name", read_only=True)

    class Meta:
        model = CaseState
        fields = ["id", "case", "status_name", "status", "state_date", "users"]


class CaseSerializer(serializers.ModelSerializer):
    address = AddressSerializer(required=True)
    case_states = CaseStateSerializer(many=True)
    current_state = CaseStateSerializer(
        source="get_current_state",
        required=False,
        read_only=True,
        allow_null=True,
    )
    team = CaseTeamSerializer(required=True)
    reason = CaseReasonSerializer(required=True)

    class Meta:
        model = Case
        fields = "__all__"


class CaseCreateUpdateSerializer(serializers.ModelSerializer):
    author = serializers.HiddenField(default=serializers.CurrentUserDefault())
    address = AddressSerializer(required=True)
    team = serializers.PrimaryKeyRelatedField(
        many=False, required=True, queryset=CaseTeam.objects.all()
    )
    reason = serializers.PrimaryKeyRelatedField(
        many=False, required=True, queryset=CaseReason.objects.all()
    )

    class Meta:
        model = Case
        fields = ("id", "address", "team", "reason", "description", "author")

    def validate(self, data):
        """
        Check CaseReason and CaseTeam relation
        """
        team = data["team"]
        reason = data["reason"]

        if reason.team != team:
            raise serializers.ValidationError(
                "reason must be one of the team CaseReasons"
            )

        return data

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

        case_state_type, _ = CaseStateType.objects.get_or_create(name=PLAN_VISIT)
        case_state, _ = CaseState.objects.get_or_create(
            case=case, status=case_state_type, state_date=datetime.now().date()
        )

        return case


class PushCaseStateSerializer(serializers.Serializer):
    user_emails = serializers.ListField(child=serializers.EmailField(), required=True)
