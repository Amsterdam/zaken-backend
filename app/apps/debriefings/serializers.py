from apps.debriefings.models import Debriefing
from rest_framework import serializers


class DebriefingSerializer(serializers.ModelSerializer):
    is_editable_until = serializers.DateTimeField(read_only=True)
    is_editable = serializers.BooleanField(read_only=True)

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
            "is_editable_until",
        )
        read_only_fields = (
            "date_added",
            "date_modified",
            "id",
            "is_editable",
            "is_editable_until",
        )


# TODO: DebriefingCreateTempSerializer and DebriefingCreateSerializer can be consolidated into the regular DebriefingSerializer
# This should be easier to do once we're not using case.identification anymore
class DebriefingCreateTempSerializer(serializers.ModelSerializer):
    is_editable_until = serializers.DateTimeField(read_only=True)
    is_editable = serializers.BooleanField(read_only=True)

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
            "is_editable_until",
        )
        read_only_fields = (
            "date_added",
            "date_modified",
            "id",
            "is_editable",
            "is_editable_until",
        )


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
