from apps.addresses.models import Address
from apps.addresses.serializers import AddressSerializer
from apps.camunda.models import CamundaProcess
from apps.cases.models import (
    Case,
    CaseReason,
    CaseState,
    CaseStateType,
    CaseTeam,
    CitizenReport,
)
from apps.schedules.serializers import ScheduleSerializer
from rest_framework import serializers


class AdvertisementLinklist(serializers.Field):
    def to_internal_value(self, data):
        return [
            li.get("advertisement_link") for li in data if li.get("advertisement_link")
        ]


class CitizenReportSerializer(serializers.ModelSerializer):
    advertisement_linklist = AdvertisementLinklist(required=False)

    class Meta:
        model = CitizenReport
        exclude = ["author"]


class CaseStateTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = CaseStateType
        fields = "__all__"


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
        fields = [
            "id",
            "case",
            "status_name",
            "status",
            "start_date",
            "end_date",
            "users",
        ]


class CaseSerializer(serializers.ModelSerializer):
    address = AddressSerializer(required=True)
    case_states = CaseStateSerializer(many=True)
    current_states = CaseStateSerializer(
        source="get_current_states",
        many=True,
        read_only=True,
    )
    team = CaseTeamSerializer(required=True)
    reason = CaseReasonSerializer(required=True)
    schedules = ScheduleSerializer(many=True, read_only=True)

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

        return case


class PushCaseStateSerializer(serializers.Serializer):
    user_emails = serializers.ListField(child=serializers.EmailField(), required=True)


class CamundaStartProcessSerializer(serializers.Serializer):
    camunda_process_id = serializers.PrimaryKeyRelatedField(
        queryset=CamundaProcess.objects.all()
    )
