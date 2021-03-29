from apps.debriefings.models import Debriefing
from rest_framework import serializers


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
