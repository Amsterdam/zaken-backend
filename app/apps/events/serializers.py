from apps.events.models import CaseEvent
from rest_framework import serializers


class CaseEventSerializer(serializers.ModelSerializer):
    event_values = serializers.JSONField()
    event_variables = serializers.JSONField()

    class Meta:
        model = CaseEvent
        fields = (
            "id",
            "event_values",
            "event_variables",
            "date_created",
            "type",
            "emitter_id",
            "case",
        )
