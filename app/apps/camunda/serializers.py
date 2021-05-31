from apps.addresses.serializers import AddressSerializer
from apps.camunda.models import CamundaProcess
from apps.cases.models import Case, CaseState
from apps.cases.serializers import CaseStateSerializer
from rest_framework import serializers


class CamundaStateWorkerSerializer(serializers.Serializer):
    """
    Serializer for Worker Data
    """

    state = serializers.CharField()
    case_identification = serializers.CharField()
    information = serializers.CharField(required=False, default="")
    case_process_id = serializers.CharField(max_length=255)

    def validate(self, data):
        try:
            Case.objects.get(id=data["case_identification"])
        except Case.DoesNotExist:
            raise serializers.ValidationError(
                "Case with the given case_identification doesn't exist"
            )
        return data

    def create(self, validated_data):
        state_name = validated_data["state"]
        case_identification = validated_data["case_identification"]
        information = validated_data["information"]
        case_process_id = validated_data["case_process_id"]

        case = Case.objects.get(id=case_identification)
        state = case.set_state(state_name, case_process_id, information)

        return state


class CamundaEndStateWorkerSerializer(serializers.Serializer):
    state_identification = serializers.PrimaryKeyRelatedField(
        queryset=CaseState.objects.all()
    )


class CamundaMessagerSerializer(serializers.Serializer):
    message_name = serializers.CharField()
    process_variables = serializers.JSONField(default={})
    case_identification = serializers.CharField()


class CamundaBaseTaskSerializer(serializers.Serializer):
    """
    Base serializer for Camunda tasks
    """

    camunda_task_id = serializers.CharField(source="id")
    # task key is used to identify specific task so for example
    # frontend knows to load a specific form when the key
    task_name_id = serializers.CharField(source="taskDefinitionKey")
    name = serializers.CharField()
    due_date = serializers.DateField(source="due")
    roles = serializers.ListField(serializers.CharField(max_length=255))


class CamundaTaskSerializer(CamundaBaseTaskSerializer):
    """
    Serializer for Camunda tasks
    """

    form = serializers.JSONField()
    render_form = serializers.CharField()
    form_variables = serializers.JSONField()


class CamundaTaskWithStateSerializer(serializers.Serializer):
    state = CaseStateSerializer()
    tasks = CamundaTaskSerializer(many=True)


class CamundaCaseAddressSerializer(serializers.ModelSerializer):
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


class CamundaTaskListSerializer(CamundaBaseTaskSerializer):
    """
    Camunda task serializer for the list-endpoint
    """

    case = CamundaCaseAddressSerializer()
    process_instance_id = serializers.CharField(source="processInstanceId")


class CamundaTaskCompleteSerializer(serializers.Serializer):
    """
    Used to complete a task in Camunda.

    variables example
    {
        "a_field": {
            "value": true,
            "label": "Label for a field"
        }
    }
    """

    author = serializers.HiddenField(default=serializers.CurrentUserDefault())
    camunda_task_id = serializers.CharField()
    case = serializers.PrimaryKeyRelatedField(queryset=Case.objects.all())
    variables = serializers.JSONField()


class CamundaDateUpdateSerializer(serializers.Serializer):
    camunda_task_id = serializers.CharField()
    date = serializers.DateTimeField(format="%Y-%m-%dT%H:%M:%S.000+0200")


class CamundaProcessSerializer(serializers.ModelSerializer):
    class Meta:
        model = CamundaProcess
        fields = "__all__"
