from apps.debriefings.models import Debriefing
from rest_framework import serializers


class DebriefingCreateSerializer(serializers.ModelSerializer):
    author = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = Debriefing
        exclude = [
            "date_added",
            "date_modified",
        ]
        read_only_fields = ("id",)


class ViolationTypeSerializer(serializers.Serializer):
    key = serializers.CharField()
