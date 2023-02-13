from apps.addresses.models import Address, HousingCorporation
from apps.addresses.serializers import AddressSerializer, AddressTinySerializer
from apps.cases.models import (
    Advertisement,
    Case,
    CaseDocument,
    CaseProject,
    CaseReason,
    CaseState,
    CaseTheme,
    Subject,
)
from apps.cases.serializers.main import (
    AdvertisementSerializer,
    CaseProjectSerializer,
    CaseReasonSerializer,
    CaseThemeSerializer,
    CitizenReportCaseSerializer,
    SubjectSerializer,
)
from apps.schedules.serializers import ScheduleDataSerializer, ScheduleSerializer
from apps.workflow.serializers import (
    CaseWorkflowBaseSerializer,
    CaseWorkflowCaseDetailSerializer,
    CaseWorkflowSerializer,
)
from drf_writable_nested.serializers import WritableNestedModelSerializer
from rest_framework import serializers


class BaseCaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Case
        exclude = (
            "identification",
            "is_legacy_bwv",
            "is_legacy_camunda",
            "legacy_bwv_case_id",
        )

    def validate(self, data):
        """
        Check CaseReason and CaseTheme relation
        """
        super().validate(data)

        theme = data.get("theme")
        reason = data.get("reason")
        project = data.get("project")

        if theme:
            if reason.theme != theme:
                raise serializers.ValidationError(
                    "reason must be one of the theme CaseReasons"
                )

            if reason.name == "Project" and not project:
                raise serializers.ValidationError("missing project for reason Project")

            if project and project.theme != theme:
                raise serializers.ValidationError(
                    "project must be one of the theme CaseReasons"
                )

        return data

    def update(self, instance, validated_data):
        if "bag_id" in validated_data:
            validated_data.pop("bag_id")
        return super().update(instance, validated_data)

    def create(self, validated_data):
        bag_id = validated_data.pop("bag_id")
        housing_corporation = validated_data.pop("housing_corporation", None)
        address = Address.get_or_create_by_bag_id(bag_id)
        if housing_corporation and not address.housing_corporation:
            address.housing_corporation = housing_corporation
            address.save()
        elif housing_corporation and address.housing_corporation != housing_corporation:
            raise Exception(
                f"You can not change the housing_corporation for a existing address: {address.housing_corporation}, new {housing_corporation}"
            )

        case = super().create(validated_data)

        case.address = address
        case.save()

        return case


class CaseSerializer(serializers.ModelSerializer):
    address = AddressTinySerializer(read_only=True)
    reason = CaseReasonSerializer(read_only=True)
    schedules = ScheduleSerializer(source="get_schedules", many=True, read_only=True)
    workflows = CaseWorkflowBaseSerializer(
        source="get_workflows", many=True, read_only=True
    )
    theme = CaseThemeSerializer(read_only=True)
    advertisements = AdvertisementSerializer(many=True, required=False)
    subjects = SubjectSerializer(many=True, read_only=True)
    project = CaseProjectSerializer(read_only=True)

    class Meta:
        model = Case
        exclude = (
            "identification",
            "is_legacy_bwv",
            "is_legacy_camunda",
            "legacy_bwv_case_id",
            "is_enforcement_request",
            "mma_number",
            "previous_case",
            "description",
            "case_url",
            "case_deleted",
            "sensitive",
            "author",
            "created",
        )


class CaseCreateSerializer(BaseCaseSerializer, WritableNestedModelSerializer):
    author = serializers.HiddenField(
        default=serializers.CurrentUserDefault(), write_only=True
    )
    address = AddressSerializer(read_only=True)
    bag_id = serializers.CharField(required=True, write_only=True)
    theme = CaseThemeSerializer(read_only=True)
    theme_id = serializers.PrimaryKeyRelatedField(
        source="theme", queryset=CaseTheme.objects.all(), write_only=True
    )
    reason = CaseReasonSerializer(read_only=True)
    reason_id = serializers.PrimaryKeyRelatedField(
        source="reason",
        required=True,
        queryset=CaseReason.objects.all(),
        write_only=True,
    )
    project = CaseProjectSerializer(read_only=True)
    project_id = serializers.PrimaryKeyRelatedField(
        source="project",
        required=False,
        queryset=CaseProject.objects.all(),
        write_only=True,
    )
    subjects = SubjectSerializer(many=True, read_only=True)
    subject_ids = serializers.PrimaryKeyRelatedField(
        required=False,
        many=True,
        write_only=True,
        queryset=Subject.objects.all(),
        source="subjects",
    )
    citizen_reports = CitizenReportCaseSerializer(
        source="case_citizen_reports", many=True, required=False
    )
    advertisements = AdvertisementSerializer(many=True, required=False)
    housing_corporation = serializers.PrimaryKeyRelatedField(
        required=False,
        queryset=HousingCorporation.objects.all(),
        write_only=True,
    )
    state = serializers.CharField(source="get_state", read_only=True)
    workflows = CaseWorkflowSerializer(
        source="get_workflows", many=True, read_only=True
    )

    def create(self, validated_data):
        case = super().create(validated_data)

        advertisements = []
        for a in case.advertisements.filter(
            related_object_id__isnull=True,
        ):
            a.related_object = case
            advertisements.append(a)
        Advertisement.objects.bulk_update(
            advertisements, ["related_object_type", "related_object_id"]
        )

        return case

    class Meta:
        model = Case
        exclude = (
            "identification",
            "is_legacy_bwv",
            "is_legacy_camunda",
            "legacy_bwv_case_id",
        )


class CaseDataSerializer(serializers.ModelSerializer):
    address = AddressSerializer(read_only=True)
    state = serializers.CharField(source="get_state", read_only=True)
    workflows = CaseWorkflowSerializer(
        source="get_workflows", many=True, read_only=True
    )
    subjects = SubjectSerializer(many=True, read_only=True)
    project = CaseProjectSerializer(read_only=True)
    theme = CaseThemeSerializer(read_only=True)
    reason = CaseReasonSerializer(read_only=True)
    schedules = ScheduleDataSerializer(many=True, read_only=True)
    advertisements = AdvertisementSerializer(many=True, required=False, read_only=True)

    class Meta:
        model = Case
        fields = "__all__"


class CaseDetailSerializer(serializers.ModelSerializer):
    address = AddressSerializer(read_only=True)
    state = serializers.CharField(source="get_state", read_only=True)
    workflows = CaseWorkflowSerializer(
        source="get_workflows", many=True, read_only=True
    )
    subjects = SubjectSerializer(many=True, read_only=True)
    project = CaseProjectSerializer(read_only=True)
    theme = CaseThemeSerializer(read_only=True)
    reason = CaseReasonSerializer(read_only=True)
    schedules = ScheduleSerializer(source="get_schedules", many=True, read_only=True)
    advertisements = AdvertisementSerializer(many=True, required=False, read_only=True)

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
            "created",
        )


class CaseDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = CaseDocument
        fields = "__all__"


class CaseDocumentUploadSerializer(serializers.Serializer):
    file = serializers.FileField()
    documenttype_url = serializers.URLField(required=False)


class DocumentTypeSerializer(serializers.Serializer):
    omschrijving = serializers.CharField()
    url = serializers.URLField()
