from apps.addresses.models import Address
from apps.addresses.serializers import AddressSerializer
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
from apps.workflow.models import CaseUserTask, CaseWorkflow, WorkflowOption
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


class CaseUserTaskCaseListSerializer(serializers.ModelSerializer):
    user_has_permission = serializers.SerializerMethodField()
    case_user_task_id = serializers.CharField(source="id")
    roles = serializers.ListSerializer(child=serializers.CharField(), required=True)

    @extend_schema_field(serializers.BooleanField)
    def get_user_has_permission(self, obj):
        request = self.context.get("request")
        if request and hasattr(request, "user"):
            return request.user.has_perm("users.perform_task")
        return False

    class Meta:
        model = CaseUserTask
        exclude = ("form",)


class CaseUserTaskSerializer(CaseUserTaskCaseListSerializer):
    form = serializers.ListSerializer(child=serializers.DictField(), required=True)
    form_variables = serializers.DictField(source="get_form_variables")

    class Meta:
        model = CaseUserTask
        fields = "__all__"


class CaseAddressSerializer(serializers.ModelSerializer):
    """
    Case-address serializer for CaseUserTasks
    """

    address = AddressSerializer()

    class Meta:
        model = Case
        fields = (
            "id",
            "address",
        )


class CaseUserTaskListSerializer(CaseUserTaskSerializer):
    case = CaseAddressSerializer()

    class Meta:
        model = CaseUserTask
        fields = "__all__"


class CaseStateSerializer(serializers.ModelSerializer):
    status_name = serializers.CharField(source="status.name", read_only=True)
    tasks = CaseUserTaskCaseListSerializer(
        source="get_tasks",
        many=True,
        read_only=True,
    )

    class Meta:
        model = CaseState
        exclude = (
            "id",
            "case",
            "case_process_id",
            "users",
            "workflow",
            "information",
        )


class CaseStateTaskSerializer(CaseStateSerializer):
    information = serializers.CharField(source="get_information", read_only=True)

    class Meta:
        model = CaseState
        fields = "__all__"


class CaseWorkflowSerializer(serializers.ModelSerializer):
    state = serializers.SerializerMethodField()
    tasks = serializers.SerializerMethodField()

    @extend_schema_field(CaseUserTaskSerializer(many=True))
    def get_tasks(self, obj):
        return CaseUserTaskSerializer(
            CaseUserTask.objects.filter(
                workflow=obj,
                completed=False,
            ).order_by("id"),
            many=True,
            context=self.context,
        ).data

    @extend_schema_field(CaseStateTaskSerializer)
    def get_state(self, obj):
        return CaseStateTaskSerializer(obj.case_states.all().order_by("id").last()).data

    class Meta:
        model = CaseWorkflow
        exclude = [
            "id",
            "case",
            "created",
            "serialized_workflow_state",
            "main_workflow",
            "workflow_type",
            "workflow_version",
            "workflow_theme_name",
            "completed",
            "parent_workflow",
            "data",
        ]


class CaseProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = CaseProject
        fields = "__all__"


class CaseSerializer(serializers.ModelSerializer):
    address = AddressSerializer(required=True)
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
        exclude = (
            "camunda_ids",
            "directing_process",
            "identification",
            "is_legacy_bwv",
            "is_legacy_camunda",
            "legacy_bwv_case_id",
        )


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

        status_name = validated_data.pop("status_name", None)

        case = Case(**validated_data, address=address)

        if status_name:
            case.status_name = status_name

        case.save()

        return case


class LegacyCaseCreateSerializer(CaseCreateUpdateSerializer):
    status_name = serializers.CharField(required=False)
    project = serializers.PrimaryKeyRelatedField(
        many=False, required=False, queryset=CaseProject.objects.all()
    )

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
            "status_name",
            "project",
        )


class LegacyCaseUpdateSerializer(CaseCreateUpdateSerializer):
    project = serializers.PrimaryKeyRelatedField(
        many=False, required=False, queryset=CaseProject.objects.all()
    )

    class Meta:
        model = Case
        fields = (
            "description",
            "author",
            "legacy_bwv_case_id",
            "is_legacy_bwv",
            "start_date",
            "project",
        )

    def validate(self, data):
        return super(serializers.ModelSerializer, self).validate(data)


class PushCaseStateSerializer(serializers.Serializer):
    user_emails = serializers.ListField(child=serializers.EmailField(), required=True)


class StartWorkflowSerializer(serializers.Serializer):
    workflow_option_id = serializers.PrimaryKeyRelatedField(
        queryset=WorkflowOption.objects.all()
    )


class BWVStatusSerializer(serializers.Serializer):
    STADIUM_ID = serializers.CharField(
        allow_null=True, allow_blank=True, required=False
    )
    WS_STA_CD_OMSCHRIJVING = serializers.CharField()
    WS_USER_MODIFIED = serializers.CharField(
        allow_null=True, allow_blank=True, required=False
    )
    WS_USER_CREATED = serializers.CharField(
        allow_null=True, allow_blank=True, required=False
    )
    WS_DATE_MODIFIED = serializers.DateTimeField(
        format="%d-%m-%Y",
        input_formats=["%Y-%m-%d"],
        allow_null=True,
        required=False,
    )
    WS_DATE_CREATED = serializers.DateTimeField(
        format="%d-%m-%Y",
        input_formats=["%Y-%m-%d"],
    )
    WS_EINDDATUM = serializers.DateTimeField(
        format="%d-%m-%Y",
        input_formats=["%Y-%m-%d"],
        allow_null=True,
        required=False,
    )
    WS_BEGINDATUM = serializers.DateTimeField(
        format="%d-%m-%Y",
        input_formats=["%Y-%m-%d"],
        allow_null=True,
        required=False,
    )


class BWVMeldingenSerializer(serializers.Serializer):
    ZAAK_ID = serializers.CharField()
    HOTLINE_MELDING_ID = serializers.CharField()

    HB_BEVINDING_TIJD = serializers.CharField(
        allow_null=True, allow_blank=True, required=False
    )
    HB_BEVINDING_DATUM = serializers.DateTimeField(
        format="%d-%m-%Y",
        input_formats=["%Y-%m-%d"],
        allow_null=True,
        required=False,
    )
    HB_TOEZ_HDR2_CODE = serializers.CharField(
        allow_null=True, allow_blank=True, required=False
    )
    HB_TOEZ_HDR1_CODE = serializers.CharField(
        allow_null=True, allow_blank=True, required=False
    )
    HB_HIT = serializers.CharField(allow_null=True, allow_blank=True, required=False)
    HB_OPMERKING = serializers.CharField(
        allow_null=True, allow_blank=True, required=False
    )

    HM_USER_MODIFIED = serializers.CharField(
        allow_null=True, allow_blank=True, required=False
    )
    HM_USER_CREATED = serializers.CharField(
        allow_null=True, allow_blank=True, required=False
    )
    HM_DATE_MODIFIED = serializers.CharField(
        allow_null=True, allow_blank=True, required=False
    )
    HM_DATE_CREATED = serializers.DateTimeField(
        format="%d-%m-%Y", input_formats=["%Y-%m-%d"]
    )
    HM_OVERTREDING_CODE = serializers.CharField(
        allow_null=True, allow_blank=True, required=False
    )
    HM_MELDING_DATUM = serializers.DateTimeField(
        format="%d-%m-%Y",
        input_formats=["%Y-%m-%d"],
        allow_null=True,
        required=False,
    )
    HM_MELDER_ANONIEM = serializers.CharField(
        allow_null=True, allow_blank=True, required=False
    )
    HM_MELDER_TELNR = serializers.CharField(
        allow_null=True, allow_blank=True, required=False
    )
    HM_MELDER_EMAILADRES = serializers.CharField(
        allow_null=True, allow_blank=True, required=False
    )
    HM_MELDER_NAAM = serializers.CharField(
        allow_null=True, allow_blank=True, required=False
    )
    HM_SITUATIE_SCHETS = serializers.CharField(
        allow_null=True, allow_blank=True, required=False
    )


class BWVCaseImportValidSerializer(serializers.Serializer):
    geschiedenis = serializers.DictField(default={})
    meldingen = serializers.DictField(default={})
    legacy_bwv_case_id = serializers.CharField()
    is_legacy_bwv = serializers.BooleanField(default=True)
    ADS_NR_VRA = serializers.CharField(
        allow_null=True, allow_blank=True, required=False
    )
    ADS_NR_VRA = serializers.CharField(
        allow_null=True, allow_blank=True, required=False
    )
    WV_BEH_CD_OMSCHRIJVING = serializers.CharField(
        allow_null=True, allow_blank=True, required=False
    )

    WV_DATE_CREATED = serializers.DateTimeField(
        format="%d-%m-%Y", input_formats=["%Y-%m-%d"]
    )
    WV_MEDEDELINGEN = serializers.CharField(allow_null=True, allow_blank=True)

    ADS_PSCD = serializers.CharField(allow_null=True, allow_blank=True, required=False)
    ADS_STRAAT_NAAM = serializers.CharField(
        allow_null=True, allow_blank=True, required=False
    )
    ADS_HSNR = serializers.CharField(allow_null=True, allow_blank=True, required=False)
    ADS_HSLT = serializers.CharField(allow_null=True, allow_blank=True, required=False)
    ADS_HSTV = serializers.CharField(allow_null=True, allow_blank=True, required=False)
    CASE_REASON = serializers.CharField()


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
