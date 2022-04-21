from apps.addresses.models import HousingCorporation
from apps.cases.models import Case, CaseProject
from apps.cases.serializers.case import BaseCaseSerializer
from django.core.cache import cache
from rest_framework import serializers


class LegacyCaseCreateSerializer(BaseCaseSerializer):
    status_name = serializers.CharField(required=False)
    project = serializers.PrimaryKeyRelatedField(
        many=False, required=False, queryset=CaseProject.objects.all()
    )
    bag_id = serializers.CharField(required=True, write_only=True)
    housing_corporation = serializers.PrimaryKeyRelatedField(
        required=False,
        allow_null=True,
        queryset=HousingCorporation.objects.all(),
        write_only=True,
    )
    subworkflow = serializers.CharField(
        required=False,
        write_only=True,
        allow_null=True,
        allow_blank=True,
    )

    class Meta:
        model = Case
        fields = (
            "address",
            "theme",
            "reason",
            "description",
            "author",
            "legacy_bwv_case_id",
            "is_legacy_bwv",
            "start_date",
            "status_name",
            "project",
            "bag_id",
            "housing_corporation",
            "subworkflow",
        )

    def create(self, validated_data):
        status_name = validated_data.pop("status_name", None)
        subworkflow = validated_data.pop("subworkflow", None)
        cached_legacy_bwv_case_key = (
            f'legacy_bwv_case_id_{validated_data.get("legacy_bwv_case_id")}_create_data'
        )
        data = {
            "status_name": status_name,
        }
        if subworkflow:
            data.update(
                {
                    "jump_to": subworkflow,
                }
            )
            if subworkflow == "summon":
                data.update(
                    {
                        "debrief_next_step": {"value": "summon"},
                    }
                )
            if subworkflow == "decision":
                data.update(
                    {
                        "debrief_next_step": {"value": "summon"},
                        "summon_next_step": {"value": "decision"},
                    }
                )
        cache.set(
            cached_legacy_bwv_case_key,
            data,
            60 * 60,
        )
        case = super().create(validated_data)
        return case


class LegacyCaseUpdateSerializer(BaseCaseSerializer):
    project = serializers.PrimaryKeyRelatedField(
        many=False, required=False, queryset=CaseProject.objects.all()
    )
    bag_id = serializers.CharField(required=True, write_only=True)

    class Meta:
        model = Case
        fields = (
            "description",
            "author",
            "legacy_bwv_case_id",
            "is_legacy_bwv",
            "start_date",
            "project",
            "bag_id",
        )

    def validate(self, data):
        return super(serializers.ModelSerializer, self).validate(data)


class PushCaseStateSerializer(serializers.Serializer):
    user_emails = serializers.ListField(child=serializers.EmailField(), required=True)


class BWVStatusSerializer(serializers.Serializer):
    STADIUM_ID = serializers.CharField(
        allow_null=True, allow_blank=True, required=False
    )
    WS_STA_CD_OMSCHRIJVING = serializers.CharField()
    WS_TOELICHTING = serializers.CharField(
        allow_null=True, allow_blank=True, required=False
    )
    WS_USER_MODIFIED = serializers.CharField(
        allow_null=True, allow_blank=True, required=False
    )
    WS_USER_CREATED = serializers.CharField(
        allow_null=True, allow_blank=True, required=False
    )
    WS_DATE_MODIFIED = serializers.DateField(
        format="%d-%m-%Y",
        input_formats=["%Y-%m-%d"],
        allow_null=True,
        required=False,
    )
    WS_DATE_CREATED = serializers.DateField(
        format="%d-%m-%Y",
        input_formats=["%Y-%m-%d"],
    )
    WS_EINDDATUM = serializers.DateField(
        format="%d-%m-%Y",
        input_formats=["%Y-%m-%d"],
        allow_null=True,
        required=False,
    )
    WS_BEGINDATUM = serializers.DateField(
        format="%d-%m-%Y",
        input_formats=["%Y-%m-%d"],
        allow_null=True,
        required=False,
    )


class BWVMeldingenSerializer(serializers.Serializer):
    ZAAK_ID = serializers.CharField(allow_null=True, allow_blank=True, required=False)
    HOTLINE_MELDING_ID = serializers.CharField()

    HB_BEVINDING_TIJD = serializers.CharField(
        allow_null=True, allow_blank=True, required=False
    )
    HB_BEVINDING_DATUM = serializers.DateTimeField(
        format="%d-%m-%Y",
        input_formats=["%Y-%m-%d"],
        allow_null=True,
        required=False,
    )
    HB_TOEZ_HDR2_CODE = serializers.CharField(
        allow_null=True, allow_blank=True, required=False
    )
    HB_TOEZ_HDR1_CODE = serializers.CharField(
        allow_null=True, allow_blank=True, required=False
    )
    HB_HIT = serializers.CharField(allow_null=True, allow_blank=True, required=False)
    HB_OPMERKING = serializers.CharField(
        allow_null=True, allow_blank=True, required=False
    )

    HM_USER_MODIFIED = serializers.CharField(
        allow_null=True, allow_blank=True, required=False
    )
    HM_USER_CREATED = serializers.CharField(
        allow_null=True, allow_blank=True, required=False
    )
    HM_DATE_MODIFIED = serializers.CharField(
        allow_null=True, allow_blank=True, required=False
    )
    HM_DATE_CREATED = serializers.DateTimeField(
        format="%d-%m-%Y", input_formats=["%Y-%m-%d"]
    )
    HM_OVERTREDING_CODE = serializers.CharField(
        allow_null=True, allow_blank=True, required=False
    )
    HM_MELDING_DATUM = serializers.DateTimeField(
        format="%d-%m-%Y",
        input_formats=["%Y-%m-%d"],
        allow_null=True,
        required=False,
    )
    HM_MELDER_ANONIEM = serializers.CharField(
        allow_null=True, allow_blank=True, required=False
    )
    HM_MELDER_TELNR = serializers.CharField(
        allow_null=True, allow_blank=True, required=False
    )
    HM_MELDER_EMAILADRES = serializers.CharField(
        allow_null=True, allow_blank=True, required=False
    )
    HM_MELDER_NAAM = serializers.CharField(
        allow_null=True, allow_blank=True, required=False
    )
    HM_SITUATIE_SCHETS = serializers.CharField(
        allow_null=True, allow_blank=True, required=False
    )


class BWVCaseImportValidSerializer(serializers.Serializer):
    geschiedenis = serializers.DictField(default={})
    meldingen = serializers.DictField(default={})
    ADS_WOCO = serializers.CharField(allow_null=True, allow_blank=True, required=False)
    legacy_bwv_case_id = serializers.CharField()
    is_legacy_bwv = serializers.BooleanField(default=True)
    ADS_NR_VRA = serializers.CharField(
        allow_null=True, allow_blank=True, required=False
    )
    ADS_NR_VRA = serializers.CharField(
        allow_null=True, allow_blank=True, required=False
    )
    WV_BEH_CD_OMSCHRIJVING = serializers.CharField(
        allow_null=True, allow_blank=True, required=False
    )

    WV_DATE_CREATED = serializers.DateTimeField(
        format="%d-%m-%Y", input_formats=["%Y-%m-%d"]
    )
    WV_MEDEDELINGEN = serializers.CharField(allow_null=True, allow_blank=True)

    ADS_PSCD = serializers.CharField(allow_null=True, allow_blank=True, required=False)
    ADS_STRAAT_NAAM = serializers.CharField(
        allow_null=True, allow_blank=True, required=False
    )
    ADS_HSNR = serializers.CharField(allow_null=True, allow_blank=True, required=False)
    ADS_HSLT = serializers.CharField(allow_null=True, allow_blank=True, required=False)
    ADS_HSTV = serializers.CharField(allow_null=True, allow_blank=True, required=False)
    CASE_REASON = serializers.CharField()
