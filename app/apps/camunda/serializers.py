from apps.camunda.models import GenericCompletedTask
from apps.camunda.services import CamundaService
from apps.cases.models import Case, CaseState, CaseStateType
from rest_framework import serializers


class CamundaStateWorkerSerializer(serializers.Serializer):
    """
    Serializer for Worker Data
    """

    state = serializers.CharField()
    case_identification = serializers.CharField()

    def validate(self, data):
        try:
            Case.objects.get(identification=data["case_identification"])
        except Case.DoesNotExist:
            raise serializers.ValidationError(
                "Case with the given case_identification doesn't exist"
            )
        return data

    def create(self, validated_data):
        state_name = validated_data["state"]
        case_identification = validated_data["case_identification"]

        case = Case.objects.get(identification=case_identification)
        state = case.set_state(state_name)

        return state


class CamundaEndStateWorkerSerializer(serializers.Serializer):
    state_identification = serializers.PrimaryKeyRelatedField(
        queryset=CaseState.objects.all()
    )


class CamundaTaskSerializer(serializers.Serializer):
    """
    Serializer for Camunda tasks
    """

    camunda_task_id = serializers.CharField(source="id")
    # task key is used to identify specific task so for example
    # frontend knows to load a specific form when the key
    task_name_id = serializers.CharField(source="taskDefinitionKey")
    name = serializers.CharField()
    due_date = serializers.DateField(source="due")
    roles = serializers.ListField(serializers.CharField(max_length=255))
    form = serializers.JSONField()


class CamundaTaskCompleteSerializer(serializers.Serializer):
    """
    Used to complete a task in Camunda.

    variables example
    {
        "a_field": {
            "value": true
        }
    }
    """

    author = serializers.HiddenField(default=serializers.CurrentUserDefault())
    camunda_task_id = serializers.CharField()
    case = serializers.PrimaryKeyRelatedField(queryset=Case.objects.all())
    variables = serializers.JSONField()


class CamundaDateUpdateSerializer(serializers.Serializer):
    camunda_task_id = serializers.CharField()
    date = serializers.DateTimeField(format="iso-8601")
