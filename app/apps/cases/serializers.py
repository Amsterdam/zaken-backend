from apps.cases.models import (
    Address,
    Case,
    CaseState,
    CaseStateType,
    CaseTimelineReaction,
    CaseTimelineSubject,
    CaseTimelineThread,
)
from rest_framework import serializers


class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = (
            "bag_id",
            "id",
            "full_address",
            "street_name",
            "number",
            "suffix_letter",
            "suffix",
            "postal_code",
            "lat",
            "lng",
            "full_address",
        )
        read_only_fields = (
            "id",
            "street_name",
            "number",
            "suffix_letter",
            "suffix",
            "postal_code",
            "lat",
            "lng",
            "full_address",
        )
        extra_kwargs = {"bag_id": {"validators": []}}


class CaseStateSerializer(serializers.ModelSerializer):
    status_name = serializers.CharField(source="status.name", read_only=True)

    class Meta:
        model = CaseState
        fields = ["case", "status_name", "status", "state_date", "users"]


class CaseSerializer(serializers.ModelSerializer):
    address = AddressSerializer(required=True)
    case_states = CaseStateSerializer(many=True)
    current_state = CaseStateSerializer(
        source="get_current_state", required=False, read_only=True
    )

    class Meta:
        model = Case
        fields = "__all__"

    def update(self, instance, validated_data):
        address_data = validated_data.pop("address", None)
        if address_data:
            address = Address.get(address_data.get("bag_id"))
            instance.address = address

        for key, value in validated_data.items():
            setattr(instance, key, value)

        instance.save()

        return instance

    def create(self, validated_data):
        address_data = validated_data.pop("address")
        address = Address.get(address_data.get("bag_id"))

        case = Case.objects.create(**validated_data, address=address)

        return case


class ResidentSerializer(serializers.Serializer):
    geboortedatum = serializers.DateTimeField(required=True)
    geslachtsaanduiding = serializers.ChoiceField(choices=("M", "V", "X"))
    geslachtsnaam = serializers.CharField(required=True)
    voorletters = serializers.CharField(required=True)
    voornamen = serializers.CharField(required=True)
    voorvoegsel_geslachtsnaam = serializers.CharField(required=False)
    datum_begin_relatie_verblijadres = serializers.DateTimeField(required=True)


class ResidentsSerializer(serializers.Serializer):
    results = ResidentSerializer(required=True, many=True)


class CaseTimelineReactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = CaseTimelineReaction
        fields = "__all__"


class CaseTimelineThreadSerializer(serializers.ModelSerializer):
    casettimelinereaction_set = CaseTimelineReactionSerializer(
        many=True, read_only=True
    )

    class Meta:
        model = CaseTimelineThread
        fields = "__all__"


class CaseTimelineSerializer(serializers.ModelSerializer):
    casetimelinethread_set = CaseTimelineThreadSerializer(many=True, read_only=True)

    class Meta:
        model = CaseTimelineSubject
        fields = "__all__"


class CaseTimelineSubjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = CaseTimelineSubject
        fields = "__all__"


class TimelineAddSerializer(serializers.Serializer):
    case_identification = serializers.CharField()
    subject = serializers.CharField()
    parameters = serializers.JSONField(allow_null=True)
    notes = serializers.CharField(allow_null=True)
    authors = serializers.CharField(allow_null=True)


class TimelineUpdateSerializer(serializers.Serializer):
    thread_id = serializers.CharField()
    subject = serializers.CharField()
    parameters = serializers.JSONField(allow_null=True)
    notes = serializers.CharField(allow_null=True)
    authors = serializers.CharField(allow_null=True)
