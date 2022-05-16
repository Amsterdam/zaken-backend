from apps.addresses.models import Address, HousingCorporation
from apps.addresses.serializers import AddressSerializer
from apps.cases.models import (
    Advertisement,
    Case,
    CaseDocument,
    CaseProject,
    CaseReason,
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
from apps.schedules.serializers import ScheduleSerializer
from apps.workflow.serializers import CaseWorkflowCaseDetailSerializer
from drf_writable_nested.serializers import WritableNestedModelSerializer
from rest_framework import serializers


class BaseCaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Case
        exclude = (
            "directing_process",
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
        address = Address.get(bag_id)
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


class CaseSerializer(BaseCaseSerializer, WritableNestedModelSerializer):
    author = serializers.HiddenField(
        default=serializers.CurrentUserDefault(), write_only=True
    )
    address = AddressSerializer(read_only=True)
    bag_id = serializers.CharField(required=True, write_only=True)
    current_states = CaseWorkflowCaseDetailSerializer(
        source="get_current_states",
        many=True,
        read_only=True,
    )
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
    schedules = ScheduleSerializer(source="get_schedules", many=True, read_only=True)
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
            "directing_process",
            "identification",
            "is_legacy_bwv",
            "is_legacy_camunda",
            "legacy_bwv_case_id",
        )


class CaseDetailSerializer(CaseSerializer):
    reason = serializers.PrimaryKeyRelatedField(
        many=False, required=True, queryset=CaseReason.objects.all()
    )
    project = serializers.PrimaryKeyRelatedField(
        many=False, required=False, queryset=CaseProject.objects.all()
    )

    class Meta:
        model = Case
        fields = (
            "id",
            "address",
            "theme",
            "reason",
            "description",
            "author",
            "project",
            "ton_ids",
            "subjects",
            "last_updated",
            "created",
        )


class CaseDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = CaseDocument
        fields = "__all__"


class CaseDocumentUploadSerializer(serializers.Serializer):
    file = serializers.FileField()
    title = serializers.CharField(required=False)
    documenttype_url = serializers.URLField(required=False)


class DocumentTypeSerializer(serializers.Serializer):
    omschrijving = serializers.CharField()
    url = serializers.URLField()
