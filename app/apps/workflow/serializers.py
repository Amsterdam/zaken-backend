from apps.addresses.serializers import AddressSerializer
from apps.cases.models import Case
from apps.cases.serializers import CaseStateTaskSerializer
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers
from rest_framework.fields import empty
from rest_framework.settings import api_settings

from .models import CaseUserTask, CaseWorkflow


class CaseUserTaskUpdateOwnerSerializer(serializers.ModelSerializer):
    class Meta:
        model = CaseUserTask
        fields = ["owner"]


class CaseUserTaskSerializer(serializers.ModelSerializer):
    user_has_permission = serializers.SerializerMethodField()
    case_user_task_id = serializers.CharField(source="id")
    form_variables = serializers.DictField(source="get_form_variables")
    # frontend dep: rename to 'task_name'
    task_name_id = serializers.CharField(source="task_name")

    @extend_schema_field(serializers.BooleanField)
    def get_user_has_permission(self, obj):
        request = self.context.get("request")
        if request and hasattr(request, "user"):
            return request.user.has_perm("users.perform_task")
        return False

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
            "data",
        ]


class WorkflowSpecConfigVerionSerializer(serializers.Serializer):
    messages = serializers.DictField(required=False, child=serializers.DictField())


class WorkflowSpecConfigThemeSerializer(serializers.Serializer):
    initial_data = serializers.DictField()
    versions = serializers.DictField(child=WorkflowSpecConfigVerionSerializer())

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
    decision = WorkflowSpecConfigThemeSerializer(required=False)
    director = WorkflowSpecConfigThemeSerializer(required=False)
    renounce_decision = WorkflowSpecConfigThemeSerializer(required=False)
    sub_workflow = WorkflowSpecConfigThemeSerializer(required=False)
    summon = WorkflowSpecConfigThemeSerializer(required=False)
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
    vakantieverhuur = WorkflowSpecConfigThemeTypeSerializer(required=False)

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
