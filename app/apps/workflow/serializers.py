from rest_framework import serializers
from rest_framework.fields import empty
from rest_framework.settings import api_settings


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
