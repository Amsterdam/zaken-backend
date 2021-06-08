from apps.addresses.models import Address
from apps.addresses.serializers import AddressSerializer
from apps.camunda.models import CamundaProcess
from apps.cases.models import (
    Case,
    CaseClose,
    CaseCloseReason,
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
    schedules = ScheduleSerializer(source="get_schedules", many=True, read_only=True)

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


class LegacyCaseCreateSerializer(CaseCreateUpdateSerializer):
    class Meta:
        model = Case
        fields = (
            "address",
            "theme",
            "reason",
            "description",
            "author",
            "legacy_bwv_case_id",
            "is_legacy_bwv",
            "start_date",
        )


class LegacyCaseUpdateSerializer(CaseCreateUpdateSerializer):
    class Meta:
        model = Case
        fields = (
            "description",
            "author",
            "legacy_bwv_case_id",
            "is_legacy_bwv",
            "start_date",
        )

    def validate(self, data):
        return super(serializers.ModelSerializer, self).validate(data)


class PushCaseStateSerializer(serializers.Serializer):
    user_emails = serializers.ListField(child=serializers.EmailField(), required=True)


class CamundaStartProcessSerializer(serializers.Serializer):
    camunda_process_id = serializers.PrimaryKeyRelatedField(
        queryset=CamundaProcess.objects.all()
    )


class BWVCaseImportValidSerializer(serializers.Serializer):
    legacy_bwv_case_id = serializers.CharField()
    is_legacy_bwv = serializers.BooleanField(default=True)
    begindatum_zaak = serializers.CharField()
    user_created_zaak = serializers.CharField()
    date_created_zaak = serializers.DateField(
        format="%d-%m-%Y", input_formats=["%d-%m-%Y"]
    )
    user_modified_zaak = serializers.CharField(allow_null=True, allow_blank=True)
    date_modified_zaak = serializers.CharField(allow_null=True, allow_blank=True)
    mededelingen = serializers.CharField(allow_null=True, allow_blank=True)
    sta_nr = serializers.FloatField()
    sta_code = serializers.CharField()
    mdr_code_stadia = serializers.CharField()
    begindatum_stadia = serializers.CharField()
    user_created_stadia = serializers.CharField()
    date_created_stadia = serializers.CharField()
    user_modified_stadia = serializers.CharField(allow_null=True, allow_blank=True)
    date_modified_stadia = serializers.CharField(allow_null=True, allow_blank=True)
    melding_datum = serializers.CharField(allow_null=True, allow_blank=True)
    mdw_code_melding = serializers.CharField(allow_null=True, allow_blank=True)
    melder_naam = serializers.CharField(allow_null=True, allow_blank=True)
    melder_emailadres = serializers.CharField(allow_null=True, allow_blank=True)
    melder_telnr = serializers.CharField(allow_null=True, allow_blank=True)
    situatie_schets = serializers.CharField(allow_null=True, allow_blank=True)
    user_created_melding = serializers.CharField(allow_null=True, allow_blank=True)
    date_created_melding = serializers.CharField(allow_null=True, allow_blank=True)
    user_modified_melding = serializers.CharField(allow_null=True, allow_blank=True)
    date_modified_melding = serializers.CharField(allow_null=True, allow_blank=True)
    postcode = serializers.CharField(allow_null=True, allow_blank=True)
    straatnaam = serializers.CharField(
        allow_null=True, allow_blank=True, required=False
    )
    huisnummer = serializers.IntegerField(allow_null=True, required=False)
    huisletter = serializers.CharField(
        allow_null=True, allow_blank=True, required=False
    )
    toev = serializers.CharField(allow_null=True, allow_blank=True, required=False)


class CaseCloseReasonSerializer(serializers.ModelSerializer):
    class Meta:
        model = CaseCloseReason
        fields = "__all__"


class CaseCloseSerializer(serializers.ModelSerializer):
    class Meta:
        model = CaseClose
        fields = "__all__"
