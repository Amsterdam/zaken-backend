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

        print("Getting case for this identification")
        case = Case.objects.get(identification=case_identification)
        print(case)
        state = case.set_state(state_name)
        print("Created state")
        print(state)

        return state


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
