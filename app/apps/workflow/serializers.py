from apps.addresses.serializers import AddressSerializer
from apps.cases.models import Case
from apps.cases.serializers import CaseStateSerializer
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

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

    @extend_schema_field(CaseStateSerializer)
    def get_state(self, obj):
        return CaseStateSerializer(obj.case_states.all().order_by("id").last()).data

    class Meta:
        model = CaseWorkflow
        exclude = [
            "id",
            "case",
            "created",
            "serialized_workflow_state",
            "main_workflow",
            "data",
        ]
