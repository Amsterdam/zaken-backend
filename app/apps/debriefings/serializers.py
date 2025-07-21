from apps.debriefings.models import Debriefing, ViolationType
from rest_framework import serializers


class DebriefingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Debriefing
        fields = "__all__"


class DebriefingCreateSerializer(serializers.ModelSerializer):
    author = serializers.HiddenField(default=serializers.CurrentUserDefault())
    nuisance_detected = serializers.BooleanField(required=False)
    violation = serializers.CharField(required=False)

    def validate(self, attrs):
        violation_value = attrs.get("violation")
        case = attrs.get("case")
        if violation_value and case:
            violation = ViolationType.objects.get(
                value=violation_value, theme_id=case.theme_id
            )
            attrs["violation"] = violation
        return attrs

    class Meta:
        model = Debriefing
        exclude = [
            "date_added",
            "date_modified",
        ]
        read_only_fields = ("id",)


class ViolationTypeSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    key = serializers.CharField()
    value = serializers.CharField()
