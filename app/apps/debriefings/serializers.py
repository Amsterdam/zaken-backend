from apps.debriefings.models import Debriefing
from rest_framework import serializers


class DebriefingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Debriefing
        fields = (
            "id",
            "case",
            "author",
            "date_added",
            "date_modified",
            "violation",
            "feedback",
        )
        read_only_fields = (
            "date_added",
            "date_modified",
            "id",
        )


class DebriefingCreateSerializer(serializers.ModelSerializer):
    author = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = Debriefing
        fields = (
            "id",
            "author",
            "violation",
            "feedback",
            "case",
        )
        read_only_fields = ("id",)
