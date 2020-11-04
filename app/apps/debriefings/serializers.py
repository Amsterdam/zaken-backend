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
            "is_editable",
        )
        read_only_fields = ("date", "id", "is_editable")


# TODO: DebriefingCreateTempSerializer and DebriefingCreateSerializer can be consolidated into the regular DebriefingSerializer
# This should be easier to do once we're not using case.identification anymore
class DebriefingCreateTempSerializer(serializers.ModelSerializer):
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
            "is_editable",
        )
        read_only_fields = ("date", "id", "is_editable")


class DebriefingCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Debriefing
        fields = (
            "id",
            "violation",
            "feedback",
            "case",
        )
        read_only_fields = ("id",)
