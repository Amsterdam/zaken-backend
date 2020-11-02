from apps.events.models import Event
from rest_framework import serializers


class EventSerializer(serializers.ModelSerializer):
    values = serializers.JSONField()

    class Meta:
        model = Event
        fields = (
            "id",
            "values",
            "date_created",
            "type",
            "emitter_id",
            "case",
        )
