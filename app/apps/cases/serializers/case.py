import logging

from apps.addresses.models import Address, HousingCorporation
from apps.addresses.serializers import (
    AddressSerializer,
    AddressSimplifiedSerializer,
    AddressTinySerializer,
)
from apps.cases.models import (
    Advertisement,
    Case,
    CaseProject,
    CaseReason,
    CaseTheme,
    Subject,
    Tag,
)
from apps.cases.serializers.main import (
    AdvertisementSerializer,
    CaseProjectSerializer,
    CaseReasonSerializer,
    CaseThemeSerializer,
    CitizenReportCaseSerializer,
    SubjectSerializer,
    TagSerializer,
)
from apps.permits.api_queries_powerbrowser import get_is_bed_and_breakfast_for_bag_id
from apps.schedules.serializers import ScheduleDataSerializer, ScheduleSerializer
from apps.workflow.jump_to import (
    JUMP_TO_KEY,
    get_jump_to_targets,
    is_jump_to_target_for_theme,
)
from apps.workflow.serializers import CaseWorkflowBaseSerializer, CaseWorkflowSerializer
from django.conf import settings
from drf_writable_nested.serializers import WritableNestedModelSerializer
from rest_framework import serializers

logger = logging.getLogger(__name__)


# The reasons that cannot be chosen when importing cases: they ask for
# something of one case (an MMA number, the report of a citizen, a listing in
# TON). Keep it the same as REASONS_NOT_FOR_IMPORT in the frontend.
REASONS_NOT_FOR_IMPORT = ("MMA", "SIG melding", "Digitaal toezicht")


def validate_jump_to_for_theme(jump_to, theme):
    """A target of jump_to may belong to some themes only (see JUMP_TO_TARGETS)."""
    if jump_to and not is_jump_to_target_for_theme(jump_to, theme):
        raise serializers.ValidationError(
            {"jump_to": "This step is not possible for the theme of the case."}
        )


def validate_case_classification(theme, reason, project):
    """
    The rules for the theme, reason and project of a new case: the reason and
    the project belong to the theme, and the reason "Project" needs a project.
    For creating one case and for importing cases in bulk.
    """
    if not theme or not reason:
        return

    if reason.theme != theme:
        raise serializers.ValidationError("reason must be one of the theme CaseReasons")

    if reason.name == "Project" and not project:
        raise serializers.ValidationError("missing project for reason Project")

    if project and project.theme != theme:
        raise serializers.ValidationError(
            "project must be one of the theme CaseReasons"
        )


class CaseFileUploadSerializer(serializers.Serializer):
    MAX_FILE_SIZE = 2 * 1024 * 1024

    file = serializers.FileField(help_text="Excel file, maximum 2 MiB.")
    dry_run = serializers.BooleanField(default=True)
    theme = CaseThemeSerializer(read_only=True)
    theme_id = serializers.PrimaryKeyRelatedField(
        source="theme", queryset=CaseTheme.objects.all(), write_only=True
    )
    reason = CaseReasonSerializer(read_only=True)
    reason_id = serializers.PrimaryKeyRelatedField(
        source="reason",
        required=False,
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
        source="subjects",
        required=False,
        many=True,
        write_only=True,
        queryset=Subject.objects.all(),
    )
    jump_to = serializers.ChoiceField(
        choices=[(t["value"], t["label"]) for t in get_jump_to_targets()],
        required=False,
        allow_null=True,
        write_only=True,
        help_text="Start the case at the first task of this subworkflow (see docs/jump_to.md)",
    )
    description = serializers.CharField(
        required=False,
        allow_blank=True,
        write_only=True,
        help_text=(
            "A short explanation for all cases, above the one of the row "
            "(the column 'toelichting')."
        ),
    )

    def validate_file(self, file):
        if file.size > self.MAX_FILE_SIZE:
            raise serializers.ValidationError("File size must not exceed 2 MiB.")
        return file

    def validate(self, data):
        # Checking the addresses (a dry run) needs only the theme. Importing
        # the cases needs what creating one case needs (CaseCreateSerializer).
        if data.get("dry_run", True):
            return data

        if data.get("reason") is None:
            raise serializers.ValidationError(
                {"reason_id": "This field is required when dry_run is false."}
            )
        if data["reason"].name in REASONS_NOT_FOR_IMPORT:
            raise serializers.ValidationError(
                {"reason_id": "This reason cannot be used to import cases."}
            )
        validate_case_classification(
            data.get("theme"), data.get("reason"), data.get("project")
        )
        validate_jump_to_for_theme(data.get("jump_to"), data.get("theme"))
        return data


class CaseFileTaskResultSerializer(serializers.Serializer):
    task_id = serializers.CharField()


class CaseFileTaskStatusSerializer(serializers.Serializer):
    task_id = serializers.CharField()
    status = serializers.CharField()
    result = serializers.DictField(allow_null=True)
    error = serializers.CharField(allow_null=True)


class CaseFileProcessResultSerializer(serializers.Serializer):
    result = serializers.DictField()


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

        # Without a reason only when partial: checking the addresses of a bulk
        # import (a dry run) before the reason is chosen.
        validate_case_classification(
            data.get("theme"), data.get("reason"), data.get("project")
        )

        return data

    def update(self, instance, validated_data):
        if "bag_id" in validated_data:
            validated_data.pop("bag_id")
        return super().update(instance, validated_data)

    def create(self, validated_data):
        bag_id = validated_data.pop("bag_id")
        housing_corporation = validated_data.pop("housing_corporation", None)
        theme = validated_data.get("theme")
        address = Address.get_or_create_by_bag_id(bag_id)
        if housing_corporation:
            address.housing_corporation = housing_corporation
            address.save()

        if theme and theme.name == settings.VAKANTIEVERHUUR_THEME:
            try:
                validated_data["is_bed_and_breakfast"] = (
                    get_is_bed_and_breakfast_for_bag_id(bag_id)
                )
            except Exception as exc:
                logger.exception(
                    "Failed to determine is_bed_and_breakfast for case creation with bag_id=%s: %s",
                    bag_id,
                    exc,
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
    tags = TagSerializer(many=True, read_only=True)
    project = CaseProjectSerializer(read_only=True)
    has_open_sensitive_case_on_address = serializers.BooleanField(read_only=True)

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
        source="subjects",
        required=False,
        many=True,
        write_only=True,
        queryset=Subject.objects.all(),
    )
    tags = TagSerializer(many=True, read_only=True)
    tag_ids = serializers.PrimaryKeyRelatedField(
        source="tags",
        required=False,
        many=True,
        write_only=True,
        queryset=Tag.objects.all(),
        allow_null=True,
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
    jump_to = serializers.ChoiceField(
        choices=[(t["value"], t["label"]) for t in get_jump_to_targets()],
        required=False,
        allow_null=True,
        write_only=True,
        help_text="Start the case at the first task of this subworkflow (see docs/jump_to.md)",
    )

    def validate(self, data):
        data = super().validate(data)
        validate_jump_to_for_theme(data.get("jump_to"), data.get("theme"))
        return data

    def create(self, validated_data):
        jump_to = validated_data.pop("jump_to", None)
        if jump_to:
            validated_data["initial_workflow_data"] = {JUMP_TO_KEY: jump_to}
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

    def update(self, instance, validated_data):
        # jump_to only applies when a case is created
        validated_data.pop("jump_to", None)
        return super().update(instance, validated_data)

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
    tags = TagSerializer(many=True, read_only=True)
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
    subjects = SubjectSerializer(many=True, read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    project = CaseProjectSerializer(read_only=True)
    workflows = CaseWorkflowSerializer(
        source="get_workflows", many=True, read_only=True
    )
    theme = CaseThemeSerializer(read_only=True)
    reason = CaseReasonSerializer(read_only=True)
    schedules = ScheduleSerializer(source="get_schedules", many=True, read_only=True)
    advertisements = AdvertisementSerializer(many=True, required=False, read_only=True)
    has_open_sensitive_case_on_address = serializers.BooleanField(read_only=True)

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


# CaseSimplifiedSerializer is used for the cases in Zakenoverzicht with just a few details.
class CaseSimplifiedSerializer(serializers.ModelSerializer):
    address = AddressSimplifiedSerializer(read_only=True)
    workflows = CaseWorkflowBaseSerializer(
        source="get_workflows", many=True, read_only=True
    )
    reason = CaseReasonSerializer(read_only=True)
    project = CaseProjectSerializer(read_only=True)
    has_open_sensitive_case_on_address = serializers.BooleanField(read_only=True)

    class Meta:
        model = Case
        fields = (
            "address",
            "end_date",
            "id",
            "reason",
            "workflows",
            "start_date",
            "last_updated",
            "project",
            "has_open_sensitive_case_on_address",
        )


class CaseBagIdsSerializer(serializers.ModelSerializer):
    bag_id = serializers.CharField(source="address.bag_id", read_only=True)
    nummeraanduiding_id = serializers.CharField(
        source="address.nummeraanduiding_id", read_only=True
    )

    class Meta:
        model = Case
        fields = (
            "id",
            "created",
            "bag_id",
            "nummeraanduiding_id",
        )


class AddressCaseListSerializer(serializers.ModelSerializer):
    """
    Beperkte zaak-weergave, uitsluitend voor het adres-endpoint
    (AddressViewSet.cases).

    BEWUSTE KEUZE: medewerkers zonder het recht
    `users.access_sensitive_dossiers` mogen op adresniveau zien
    dat er zaken (incl. sensitive) lopen, maar niet de details. Daarom
    bevat deze serializer alleen een minimale veldenset. Voeg hier geen
    velden toe zonder te toetsen of die informatie over sensitive zaken
    mag lekken naar gebruikers zonder dat recht. Detailtoegang blijft
    afgeschermd via CaseViewSet.get_queryset (exclude sensitive) en
    CanAccessSensitiveCases.
    """

    advertisements = AdvertisementSerializer(many=True, required=False)
    reason = CaseReasonSerializer(read_only=True)
    theme = CaseThemeSerializer(read_only=True)
    workflows = CaseWorkflowBaseSerializer(
        source="get_workflows", many=True, read_only=True
    )

    class Meta:
        model = Case
        fields = (
            "id",
            "advertisements",
            "start_date",
            "end_date",
            "theme",
            "workflows",
            "reason",
            "ton_ids",
        )
