from apps.cases.models import Case
from rest_framework import serializers
from rest_framework.fields import empty
from rest_framework.settings import api_settings

from .models import WorkflowOption


class GenericCompletedTaskSerializer(serializers.Serializer):
    """
    Used to complete a GenericCompletedTask.

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


class WorkflowOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkflowOption
        fields = "__all__"


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
    closing_procedure = WorkflowSpecConfigThemeSerializer(required=False)
    debrief = WorkflowSpecConfigThemeSerializer(required=False)
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
    holiday_rental = WorkflowSpecConfigThemeTypeSerializer(required=False)

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
