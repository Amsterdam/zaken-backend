from rest_framework import serializers


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
    roles = serializers.CharField(source="roles")


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

    camunda_task_id = serializers.CharField(source="id")
    variables = serializers.JSONField()
