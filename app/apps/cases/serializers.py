from apps.addresses.models import Address
from apps.addresses.serializers import AddressSerializer
from apps.camunda.models import CamundaProcess
from apps.cases.models import (
    Case,
    CaseReason,
    CaseState,
    CaseStateType,
    CaseTheme,
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


class CaseThemeSerializer(serializers.ModelSerializer):
    class Meta:
        model = CaseTheme
        fields = "__all__"


class CaseReasonSerializer(serializers.ModelSerializer):
    class Meta:
        model = CaseReason
        fields = "__all__"


class CaseStateSerializer(serializers.ModelSerializer):
    status_name = serializers.CharField(source="status.name", read_only=True)

    class Meta:
        model = CaseState
        fields = "__all__"


class CaseSerializer(serializers.ModelSerializer):
    address = AddressSerializer(required=True)
    case_states = CaseStateSerializer(many=True)
    current_states = CaseStateSerializer(
        source="get_current_states",
        many=True,
        read_only=True,
    )
    theme = CaseThemeSerializer(required=True)
    reason = CaseReasonSerializer(required=True)
    schedules = ScheduleSerializer(many=True, read_only=True)

    class Meta:
        model = Case
        fields = "__all__"


class CaseCreateUpdateSerializer(serializers.ModelSerializer):
    author = serializers.HiddenField(default=serializers.CurrentUserDefault())
    address = AddressSerializer(required=True)
    theme = serializers.PrimaryKeyRelatedField(
        many=False, required=True, queryset=CaseTheme.objects.all()
    )
    reason = serializers.PrimaryKeyRelatedField(
        many=False, required=True, queryset=CaseReason.objects.all()
    )

    class Meta:
        model = Case
        fields = ("id", "address", "theme", "reason", "description", "author")

    def validate(self, data):
        """
        Check CaseReason and CaseTheme relation
        """
        theme = data["theme"]
        reason = data["reason"]

        if reason.theme != theme:
            raise serializers.ValidationError(
                "reason must be one of the theme CaseReasons"
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
