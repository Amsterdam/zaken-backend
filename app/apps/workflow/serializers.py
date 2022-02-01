import re

from apps.addresses.serializers import AddressSerializer
from apps.cases.models import Case, CaseStateType
from apps.workflow.models import CaseUserTask, CaseWorkflow
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers
from rest_framework.fields import empty
from rest_framework.settings import api_settings

from .models import GenericCompletedTask, WorkflowOption


class GenericFormFieldOptionSerializer(serializers.Serializer):
    label = serializers.CharField()
    value = serializers.CharField()


class GenericFormFieldSerializer(serializers.Serializer):
    name = serializers.CharField()
    label = serializers.CharField()
    options = GenericFormFieldOptionSerializer(many=True, required=False)
    type = serializers.ChoiceField(
        choices=(("text", "text"), ("select", "select"), ("checkbox", "checkbox"))
    )
    tooltip = serializers.CharField(required=False)
    required = serializers.BooleanField()


class CaseStateTypeSerializer(serializers.ModelSerializer):
    status_name = serializers.CharField(source="name", read_only=True)

    class Meta:
        model = CaseStateType
        exclude = ("theme",)


class CaseUserTaskBaseSerializer(serializers.ModelSerializer):
    user_has_permission = serializers.SerializerMethodField()
    roles = serializers.ListSerializer(child=serializers.CharField(), required=True)

    @extend_schema_field(serializers.BooleanField)
    def get_user_has_permission(self, obj):
        request = self.context.get("request")
        if request and hasattr(request, "user"):
            return request.user.has_perm("users.perform_task")
        return False

    class Meta:
        model = CaseUserTask
        exclude = (
            "id",
            "form",
            "workflow",
            "task_name",
            "completed",
            "task_id",
            "case_user_task_id",
        )


class CaseUserTaskSerializer(CaseUserTaskBaseSerializer):
    case_user_task_id = serializers.CharField(source="id")
    form = GenericFormFieldSerializer(many=True)
    form_variables = serializers.DictField(source="get_form_variables")

    class Meta:
        model = CaseUserTask
        exclude = (
            "id",
            "completed",
            "created",
            "task_id",
            "updated",
            "workflow",
        )


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
            "sensitive",
        )


class CaseUserTaskListSerializer(CaseUserTaskBaseSerializer):
    case = CaseAddressSerializer()

    class Meta:
        model = CaseUserTask
        exclude = (
            "form",
            "workflow",
            "task_name",
            "completed",
            "task_id",
        )


class CaseWorkflowCaseDetailSerializer(serializers.ModelSerializer):
    status_name = serializers.CharField(source="case_state_type.name", read_only=True)
    status = serializers.IntegerField(source="case_state_type.id", read_only=True)
    start_date = serializers.DateTimeField(source="date_modified", read_only=True)

    class Meta:
        model = CaseWorkflow
        exclude = (
            "id",
            "case",
            "parent_workflow",
            "main_workflow",
            "workflow_type",
            "workflow_theme_name",
            "workflow_message_name",
            "created",
            "date_modified",
            "started",
            "serialized_workflow_state",
            "data",
            "completed",
            "workflow_version",
            "case_state_type",
        )


class CaseWorkflowSerializer(serializers.ModelSerializer):
    state = serializers.SerializerMethodField()
    tasks = serializers.SerializerMethodField()
    information = serializers.SerializerMethodField()

    def get_information(self, obj):
        return obj.data.get("names", {}).get("value", "")

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

    @extend_schema_field(CaseStateTypeSerializer)
    def get_state(self, obj):
        return CaseStateTypeSerializer(obj.case_state_type).data

    class Meta:
        model = CaseWorkflow
        exclude = [
            "id",
            "case",
            "created",
            "started",
            "serialized_workflow_state",
            "main_workflow",
            "workflow_type",
            "workflow_version",
            "workflow_theme_name",
            "completed",
            "parent_workflow",
            "data",
            "workflow_message_name",
            "case_state_type",
            "date_modified",
        ]


class GenericCompletedTaskSerializer(serializers.ModelSerializer):
    """
    Used to complete a GenericCompletedTask.

    variables example
    {
        "a_field": {
            "value": true,
            "label": "Label for a field"
        }
    }
    """

    author = serializers.HiddenField(default=serializers.CurrentUserDefault())
    case_user_task_id = serializers.CharField()
    case = serializers.PrimaryKeyRelatedField(queryset=Case.objects.all())
    variables = serializers.JSONField()
    description = serializers.CharField(required=False)

    class Meta:
        model = GenericCompletedTask
        fields = "__all__"


class WorkflowOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkflowOption
        fields = "__all__"


class StartWorkflowSerializer(serializers.Serializer):
    workflow_option_id = serializers.PrimaryKeyRelatedField(
        queryset=WorkflowOption.objects.all()
    )


class WorkflowSpecConfigVerionSerializer(serializers.Serializer):
    messages = serializers.DictField(required=False, child=serializers.DictField())


class WorkflowSpecConfigVerionListSerializer(serializers.DictField):
    def run_validation(self, data=empty):
        def validate_field(field):
            return bool(re.match(r"(\d+\.)+(\d+\.)+(\d+)", field))

        if data is not empty:
            not_valid = [f for f in set(data) if not validate_field(f)]
            if not_valid:
                raise serializers.ValidationError(
                    f"Versioning incorrect: {', '.join(not_valid)}"
                )

        return super().run_validation(data)


class WorkflowSpecConfigThemeSerializer(serializers.Serializer):
    initial_data = serializers.DictField()
    versions = WorkflowSpecConfigVerionListSerializer(
        child=WorkflowSpecConfigVerionSerializer()
    )

    def run_validation(self, data=empty):
        if data is not empty:
            unknown = set(data) - set(self.fields)
            if unknown:
                errors = ["Unknown field: {}".format(f) for f in unknown]
                raise serializers.ValidationError(
                    {
                        api_settings.NON_FIELD_ERRORS_KEY: errors,
                    }
                )

        return super().run_validation(data)


class WorkflowSpecConfigThemeTypeSerializer(serializers.Serializer):
    close_case = WorkflowSpecConfigThemeSerializer(required=False)
    closing_procedure = WorkflowSpecConfigThemeSerializer(required=False)
    debrief = WorkflowSpecConfigThemeSerializer(required=False)
    decision = WorkflowSpecConfigThemeSerializer(required=False)
    digital_surveillance = WorkflowSpecConfigThemeSerializer(required=False)
    director = WorkflowSpecConfigThemeSerializer(required=False)
    housing_corporation = WorkflowSpecConfigThemeSerializer(required=False)
    renounce_decision = WorkflowSpecConfigThemeSerializer(required=False)
    sub_workflow = WorkflowSpecConfigThemeSerializer(required=False)
    summon = WorkflowSpecConfigThemeSerializer(required=False)
    unoccupied = WorkflowSpecConfigThemeSerializer(required=False)
    visit = WorkflowSpecConfigThemeSerializer(required=False)

    def run_validation(self, data=empty):
        if data is not empty:
            unknown = set(data) - set(self.fields)
            if unknown:
                errors = ["Unknown field: {}".format(f) for f in unknown]
                raise serializers.ValidationError(
                    {
                        api_settings.NON_FIELD_ERRORS_KEY: errors,
                    }
                )

        return super().run_validation(data)


class WorkflowSpecConfigSerializer(serializers.Serializer):
    default = WorkflowSpecConfigThemeTypeSerializer()
    holiday_rental = WorkflowSpecConfigThemeTypeSerializer(required=False)

    def run_validation(self, data=empty):
        if data is not empty:
            unknown = set(data) - set(self.fields)
            if unknown:
                errors = ["Unknown field: {}".format(f) for f in unknown]
                raise serializers.ValidationError(
                    {
                        api_settings.NON_FIELD_ERRORS_KEY: errors,
                    }
                )

        return super().run_validation(data)
