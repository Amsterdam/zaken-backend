from apps.cases.models import (
    Advertisement,
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


class AdvertisementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Advertisement
        exclude = (
            "case",
            "related_object_type",
            "related_object_id",
        )


class CitizenReportBaseSerializer(serializers.ModelSerializer):
    author = serializers.HiddenField(default=serializers.CurrentUserDefault())
    advertisements = AdvertisementSerializer(many=True, required=False)

    def create(self, validated_data):
        advertisements = validated_data.pop("advertisements", [])
        instance = super().create(validated_data)
        advertisements = [
            Advertisement(
                **{
                    "case": instance.case,
                    "related_object": instance,
                    "link": a.get("link"),
                }
            )
            for a in advertisements
        ]
        Advertisement.objects.bulk_create(advertisements)
        return instance

    class Meta:
        model = CitizenReport
        fields = "__all__"


class CitizenReportCaseSerializer(CitizenReportBaseSerializer):
    class Meta:
        model = CitizenReport
        exclude = ["case"]


class CitizenReportSerializer(CitizenReportBaseSerializer):
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
