from apps.debriefings.models import Debriefing
from rest_framework import serializers


class DebriefingSerializer(serializers.ModelSerializer):
    case_identification = serializers.CharField(
        read_only=True, source="case.identification"
    )

    class Meta:
        model = Debriefing
        fields = (
            "case",
            "case_identification",
            "author",
            "date_added",
            "date_modified",
            "violation",
            "feedback",
        )
        read_only_fields = ("date",)


class DebriefingCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Debriefing
        fields = (
            "violation",
            "feedback",
            "case",
        )
