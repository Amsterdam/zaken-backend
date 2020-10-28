from apps.debriefings.models import Debriefing
from rest_framework import serializers


class DebriefingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Debriefing
        fields = (
            "case",
            "author",
            "date_added",
            "date_modified",
            "violation",
            "feedback",
        )
        read_only_fields = ("date",)


# TODO: Temp
class DebriefingCreateTempSerializer(serializers.ModelSerializer):
    class Meta:
        model = Debriefing
        fields = (
            "case",
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
