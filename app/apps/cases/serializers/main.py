from apps.cases.models import (
    Case,
    CaseClose,
    CaseCloseReason,
    CaseCloseResult,
    CaseProject,
    CaseReason,
    CaseTheme,
    CitizenReport,
    Subject,
)
from rest_framework import serializers


class AdvertisementLinklist(serializers.Field):
    def to_representation(self, value):
        return value

    def to_internal_value(self, data):
        return [
            li.get("advertisement_link") for li in data if li.get("advertisement_link")
        ]


class CitizenReportCaseSerializer(serializers.ModelSerializer):
    author = serializers.HiddenField(default=serializers.CurrentUserDefault())
    advertisement_linklist = AdvertisementLinklist(required=False)

    class Meta:
        model = CitizenReport
        exclude = ["case"]


class CitizenReportSerializer(serializers.ModelSerializer):
    author = serializers.HiddenField(default=serializers.CurrentUserDefault())
    advertisement_linklist = AdvertisementLinklist(required=False)

    class Meta:
        model = CitizenReport
        fields = "__all__"


class CaseThemeSerializer(serializers.ModelSerializer):
    class Meta:
        model = CaseTheme
        fields = "__all__"


class CaseReasonSerializer(serializers.ModelSerializer):
    class Meta:
        model = CaseReason
        fields = "__all__"


class CaseProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = CaseProject
        fields = "__all__"


class SubjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subject
        fields = "__all__"


class CaseCloseReasonSerializer(serializers.ModelSerializer):
    class Meta:
        model = CaseCloseReason
        fields = "__all__"


class CaseCloseResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = CaseCloseResult
        fields = "__all__"


class CaseCloseSerializer(serializers.ModelSerializer):
    author = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = CaseClose
        fields = "__all__"

    def validate(self, data):
        # Validate if result's Theme equals the case's theme
        if data.get("result"):
            if data["case"].theme != data["result"].case_theme:
                raise serializers.ValidationError(
                    "Themes don't match between result and case"
                )

        if data["reason"].result:
            # If the reason is a result, the result should be populated
            if not data.get("result"):
                raise serializers.ValidationError("result not found")

            # Validate if Reason Theme equals the Case Theme
            if data["case"].theme != data["reason"].case_theme:
                raise serializers.ValidationError(
                    "Themes don't match between reason and case"
                )

        else:
            # Make sure we ignore the result in case the Reason isn't a result
            data["result"] = None

        return data