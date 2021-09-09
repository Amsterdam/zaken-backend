from apps.addresses.serializers import AddressSerializer
from apps.cases.models import Case
from apps.cases.serializers import CaseStateSerializer
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from .models import Task, Workflow


class TaskSerializer(serializers.ModelSerializer):
    user_has_permission = serializers.SerializerMethodField()
    camunda_task_id = serializers.CharField(source="id")
    form_variables = serializers.Serializer(source="get_form_variables")

    @extend_schema_field(serializers.BooleanField)
    def get_user_has_permission(self, obj):
        return True  # self.request.user.has_perm("users.perform_task")

    class Meta:
        model = Task
        fields = "__all__"


class CaseAddressSerializer(serializers.ModelSerializer):
    """
    Case-address serializer for camunda tasks
    """

    address = AddressSerializer()

    class Meta:
        model = Case
        fields = (
            "id",
            "address",
        )


class TaskListSerializer(serializers.ModelSerializer):
    case = CaseAddressSerializer()
    user_has_permission = serializers.SerializerMethodField()
    camunda_task_id = serializers.CharField(source="id")

    @extend_schema_field(serializers.BooleanField)
    def get_user_has_permission(self, obj):
        return True  # self.request.user.has_perm("users.perform_task")

    class Meta:
        model = Task
        fields = "__all__"


class WorkflowSerializer(serializers.ModelSerializer):
    state = serializers.SerializerMethodField()
    tasks = serializers.SerializerMethodField()

    @extend_schema_field(TaskSerializer)
    def get_tasks(self, obj):
        return TaskSerializer(
            Task.objects.filter(
                workflow=obj,
                completed=False,
            ),
            many=True,
        ).data

    @extend_schema_field(CaseStateSerializer)
    def get_state(self, obj):
        return CaseStateSerializer(obj.case_states.all().order_by("id").last()).data

    class Meta:
        model = Workflow
        exclude = [
            "id",
            "case",
            "serialized_workflow_state",
            "workflow_spec",
        ]
