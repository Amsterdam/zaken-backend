from apps.addresses.serializers import AddressSerializer
from apps.cases.models import Case
from apps.cases.serializers import CaseStateTaskSerializer
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers
from rest_framework.fields import empty
from rest_framework.settings import api_settings

from .models import CaseUserTask, CaseWorkflow


class CaseUserTaskSerializer(serializers.ModelSerializer):
    user_has_permission = serializers.SerializerMethodField()
    camunda_task_id = serializers.CharField(source="id")
    form_variables = serializers.DictField(source="get_form_variables")
    # frontend dep: rename to 'task_name'
    task_name_id = serializers.CharField(source="task_name")

    @extend_schema_field(serializers.BooleanField)
    def get_user_has_permission(self, obj):
        return True  # self.request.user.has_perm("users.perform_task")

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


class CaseWorkflowSerializer(serializers.ModelSerializer):
    state = serializers.SerializerMethodField()
    tasks = serializers.SerializerMethodField()

    @extend_schema_field(CaseUserTaskSerializer)
    def get_tasks(self, obj):
        return CaseUserTaskSerializer(
            CaseUserTask.objects.filter(
                workflow=obj,
                completed=False,
            ).order_by("id"),
            many=True,
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
            "data",
        ]


class CharFieldStringOnly(serializers.CharField):
    def to_internal_value(self, data):
        if isinstance(data, bool) or not isinstance(data, (str,)):
            self.fail("invalid")
        value = str(data)
        return value.strip() if self.trim_whitespace else value


class WorkflowSpecConfigVerionSerializer(serializers.Serializer):
    messages = serializers.ListSerializer(required=False, child=CharFieldStringOnly())


class WorkflowSpecConfigThemeSerializer(serializers.Serializer):
    close_case = serializers.DictField(
        required=False, child=WorkflowSpecConfigVerionSerializer()
    )
    decision = serializers.DictField(
        required=False, child=WorkflowSpecConfigVerionSerializer()
    )
    director = serializers.DictField(
        required=False, child=WorkflowSpecConfigVerionSerializer()
    )
    renounce_decision = serializers.DictField(
        required=False, child=WorkflowSpecConfigVerionSerializer()
    )
    sub_workflow = serializers.DictField(
        required=False, child=WorkflowSpecConfigVerionSerializer()
    )
    summon = serializers.DictField(
        required=False, child=WorkflowSpecConfigVerionSerializer()
    )
    visit = serializers.DictField(
        required=False, child=WorkflowSpecConfigVerionSerializer()
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


class WorkflowSpecConfigSerializer(serializers.Serializer):
    default = WorkflowSpecConfigThemeSerializer()
    vakantieverhuur = WorkflowSpecConfigThemeSerializer(required=False)

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
