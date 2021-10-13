from apps.camunda.models import CamundaProcess
from apps.cases.models import Case
from rest_framework import serializers


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
    case_user_task_id = serializers.CharField()
    case = serializers.PrimaryKeyRelatedField(queryset=Case.objects.all())
    variables = serializers.JSONField()


class CamundaProcessSerializer(serializers.ModelSerializer):
    class Meta:
        model = CamundaProcess
        fields = "__all__"
