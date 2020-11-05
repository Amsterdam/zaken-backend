from apps.events.models import CaseEvent
from rest_framework import serializers


class CaseEventSerializer(serializers.ModelSerializer):
    event_values = serializers.JSONField()

    class Meta:
        model = CaseEvent
        fields = (
            "id",
            "event_values",
            "date_created",
            "type",
            "emitter_id",
            "emitter_is_editable",
            "case",
        )
