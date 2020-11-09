from apps.events.models import CaseEvent
from rest_framework import serializers


class CaseEventSerializer(serializers.ModelSerializer):
    event_values = serializers.JSONField()
    emitter_is_editable_until = serializers.DateTimeField()
    emitter_is_editable = serializers.BooleanField()

    class Meta:
        model = CaseEvent
        fields = (
            "id",
            "event_values",
            "date_created",
            "type",
            "emitter_id",
            "emitter_is_editable",
            "emitter_is_editable_until",
            "case",
        )
