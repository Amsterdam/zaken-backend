from rest_framework import serializers


class CamundaTaskSerializer(serializers.Serializer):
    """
    Serializer for Camunda tasks
    """

    task_id = serializers.CharField(source="id")
    # task key is used to identify specific task so for example
    # frontend knows to load a specific form when the key
    task_key = serializers.CharField(source="taskDefinitionKey")
    name = serializers.CharField()
