from apps.debriefings.models import Debriefing
from rest_framework import serializers


class DebriefingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Debriefing
        fields = "__all__"


class DebriefingCreateSerializer(serializers.ModelSerializer):
    author = serializers.HiddenField(default=serializers.CurrentUserDefault())
    nuisance_detected = serializers.BooleanField(required=False)

    class Meta:
        model = Debriefing
        exclude = [
            "date_added",
            "date_modified",
        ]
        read_only_fields = ("id",)


class ViolationTypeSerializer(serializers.Serializer):
    key = serializers.CharField()
    value = serializers.CharField()
