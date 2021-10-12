from apps.addresses.models import Address
from apps.addresses.serializers import AddressSerializer
from apps.camunda.models import CamundaProcess
from apps.cases.models import (
    Case,
    CaseClose,
    CaseCloseReason,
    CaseCloseResult,
    CaseProject,
    CaseReason,
    CaseState,
    CaseStateType,
    CaseTheme,
    CitizenReport,
)
from apps.schedules.serializers import ScheduleSerializer
from apps.workflow.models import CaseUserTask
from apps.workflow.tasks import start_case_with_workflow
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers


class AdvertisementLinklist(serializers.Field):
    def to_internal_value(self, data):
        return [
            li.get("advertisement_link") for li in data if li.get("advertisement_link")
        ]


class CitizenReportSerializer(serializers.ModelSerializer):
    author = serializers.HiddenField(default=serializers.CurrentUserDefault())
    advertisement_linklist = AdvertisementLinklist(required=False)

    class Meta:
        model = CitizenReport
        fields = "__all__"


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


class CaseUserTaskSerializer(serializers.ModelSerializer):
    user_has_permission = serializers.SerializerMethodField()
    camunda_task_id = serializers.CharField(source="id")

    @extend_schema_field(serializers.BooleanField)
    def get_user_has_permission(self, obj):
        return True  # self.request.user.has_perm("users.perform_task")

    class Meta:
        model = CaseUserTask
        fields = "__all__"


class CaseStateSerializer(serializers.ModelSerializer):
    status_name = serializers.CharField(source="status.name", read_only=True)
    tasks = CaseUserTaskSerializer(
        source="get_tasks",
        many=True,
        read_only=True,
    )

    class Meta:
        model = CaseState
        exclude = ("information",)


class CaseStateTaskSerializer(CaseStateSerializer):
    information = serializers.CharField(source="get_information", read_only=True)

    class Meta:
        model = CaseState
        fields = "__all__"


class CaseProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = CaseProject
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
    project = CaseProjectSerializer()

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
    project = serializers.PrimaryKeyRelatedField(
        many=False, required=False, queryset=CaseProject.objects.all()
    )

    class Meta:
        model = Case
        fields = (
            "id",
            "address",
            "theme",
            "reason",
            "description",
            "author",
            "project",
            "ton_ids",
        )

    def validate(self, data):
        """
        Check CaseReason and CaseTheme relation
        """
        theme = data["theme"]
        reason = data["reason"]
        project = data.get("project")

        if reason.theme != theme:
            raise serializers.ValidationError(
                "reason must be one of the theme CaseReasons"
            )

        if reason.name == "Project" and not project:
            raise serializers.ValidationError("missing project for reason Project")

        if project and project.theme != theme:
            raise serializers.ValidationError(
                "project must be one of the theme CaseReasons"
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

        case = start_case_with_workflow(validated_data, address)

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
    ADS_NR_VRA = serializers.CharField()
    OBJ_NR_VRA = serializers.CharField()
    begindatum_zaak = serializers.CharField()
    user_created_zaak = serializers.CharField()
    date_created_zaak = serializers.DateTimeField(
        format="%d-%m-%Y", input_formats=["%d-%m-%Y %H:%M:%S"]
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


class CaseCloseResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = CaseCloseResult
        fields = "__all__"


class CaseCloseSerializer(serializers.ModelSerializer):
    author = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = CaseClose
        fields = "__all__"

    def validate(self, data):
        # Validate if result's Theme equals the case's theme
        if data.get("result"):
            if data["case"].theme != data["result"].case_theme:
                raise serializers.ValidationError(
                    "Themes don't match between result and case"
                )

        if data["reason"].result:
            # If the reason is a result, the result should be populated
            if not data.get("result"):
                raise serializers.ValidationError("result not found")

            # Validate if Reason Theme equals the Case Theme
            if data["case"].theme != data["reason"].case_theme:
                raise serializers.ValidationError(
                    "Themes don't match between reason and case"
                )

        else:
            # Make sure we ignore the result in case the Reason isn't a result
            data["result"] = None

        return data
