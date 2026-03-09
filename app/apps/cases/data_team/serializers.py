from apps.addresses.models import Address, District
from apps.cases.models import (
    Advertisement,
    Case,
    CaseProject,
    CaseReason,
    CaseTheme,
    Subject,
    Tag,
)
from apps.schedules.models import Priority, Schedule
from rest_framework import serializers


class AddressDistrictSerializer(serializers.ModelSerializer):
    class Meta:
        model = District
        fields = "__all__"


class AddressSerializer(serializers.ModelSerializer):
    district = AddressDistrictSerializer()

    class Meta:
        model = Address
        fields = (
            "bag_id",
            "district",
            "full_address",
            "housing_corporation",
            "id",
            "lat",
            "lng",
            "number",
            "nummeraanduiding_id",
            "postal_code",
            "street_name",
            "suffix",
            "suffix_letter",
        )
        read_only_fields = (
            "district",
            "full_address",
            "id",
            "lat",
            "lng",
            "number",
            "postal_code",
            "street_name",
            "suffix",
            "suffix_letter",
        )
        ref_name = "DataTeamAddress"


class AdvertisementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Advertisement
        exclude = (
            "case",
            "related_object_type",
            "related_object_id",
        )
        ref_name = "DataTeamAdvertisement"


class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = CaseProject
        exclude = (
            "theme",
            "active",
        )


class ReasonSerializer(serializers.ModelSerializer):
    class Meta:
        model = CaseReason
        exclude = ("theme",)


class ThemeSerializer(serializers.ModelSerializer):
    class Meta:
        model = CaseTheme
        exclude = (
            "case_type_url",
            "sensitive",
        )


class SchedulePrioritySerializer(serializers.ModelSerializer):
    class Meta:
        model = Priority
        fields = ("weight",)


class ScheduleSerializer(serializers.ModelSerializer):
    priority = SchedulePrioritySerializer(required=True)

    class Meta:
        model = Schedule
        exclude = (
            "action",
            "author",
            "case",
            "case_user_task_id",
            "date_added",
            "date_modified",
            "day_segment",
            "description",
            "housing_corporation_combiteam",
            "id",
            "visit_from_datetime",
            "week_segment",
        )
        ref_name = "DataTeamSchedule"


class SubjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subject
        exclude = ("theme",)
        ref_name = "DataTeamSubject"


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        exclude = ("theme",)
        ref_name = "DataTeamTag"


class DataTeamCaseSerializer(serializers.ModelSerializer):
    advertisements = AdvertisementSerializer(many=True, required=False, read_only=True)
    address = AddressSerializer(read_only=True)
    project = ProjectSerializer(read_only=True)
    reason = ReasonSerializer(read_only=True)
    schedules = ScheduleSerializer(many=True, read_only=True)
    state = serializers.CharField(source="get_state", read_only=True)
    subjects = SubjectSerializer(many=True, read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    theme = ThemeSerializer(read_only=True)

    class Meta:
        model = Case
        exclude = (
            "identification",
            "is_legacy_bwv",
            "is_legacy_camunda",
            "legacy_bwv_case_id",
            "case_url",
            "case_deleted",
            "author",
            "previous_case",
        )
