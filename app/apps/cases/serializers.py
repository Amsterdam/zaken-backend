from apps.cases.models import (
    Address,
    Case,
    CaseTimelineReaction,
    CaseTimelineSubject,
    CaseTimelineThread,
    CaseType,
    State,
    StateType,
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


class StateTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = StateType
        fields = "__all__"
        read_only_fields = ("id",)


class StateSerializer(serializers.ModelSerializer):
    state_type = StateTypeSerializer(required=True)

    class Meta:
        model = State
        fields = "__all__"
        read_only_fields = ("id",)


class CaseTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = CaseType
        fields = "__all__"
        read_only_fields = ("id",)
        extra_kwargs = {"name": {"validators": []}}


class CaseSerializer(serializers.ModelSerializer):
    case_type = CaseTypeSerializer(required=True)
    address = AddressSerializer(required=True)
    states = StateSerializer(many=True, read_only=True)

    class Meta:
        model = Case
        fields = "__all__"

    def update(self, instance, validated_data):
        case_type_data = validated_data.pop("case_type", None)
        address_data = validated_data.pop("address", None)

        if case_type_data:
            case_type = CaseType.get(case_type_data.get("name"))
            instance.case_type = case_type

        if address_data:
            address = Address.get(address_data.get("bag_id"))
            instance.address = address

        for key, value in validated_data.items():
            setattr(instance, key, value)

        instance.save()

        return instance

    def create(self, validated_data):
        case_type_data = validated_data.pop("case_type")
        case_type = CaseType.get(case_type_data.get("name"))

        address_data = validated_data.pop("address")
        address = Address.get(address_data.get("bag_id"))

        case = Case.objects.create(
            **validated_data, case_type=case_type, address=address
        )

        return case


class FineSerializer(serializers.Serializer):
    # TODO: The official specifications for the max length is 15, but for our own cases we are using longer identification numbers
    # TODO: Refactor the identification numbers of our own cases.
    identificatienummer = serializers.CharField(max_length=64)
    vorderingnummer = serializers.IntegerField()
    jaar = serializers.IntegerField(max_value=9999)
    soort_vordering = serializers.ChoiceField(choices=("PBF", "PBN", "PRV", "SOC"))
    omschrijving_soort_vordering = serializers.CharField(max_length=50)
    indicatie_publiekrechtelijk = serializers.ChoiceField(choices=("J", "N"))
    subjectnr = serializers.IntegerField(max_value=9999999999)
    opgemaaktenaam = serializers.CharField(max_length=4000)
    subjectnr_opdrachtgever = serializers.IntegerField()
    opgemaaktenaam_opdrachtgever = serializers.CharField(max_length=4000)
    runnr = serializers.IntegerField()
    omschrijving_run = serializers.CharField(max_length=40)
    code_runwijze = serializers.CharField(max_length=3)
    omschrijving_runwijze = serializers.CharField(max_length=40)
    dagtekening = serializers.DateTimeField()
    vervaldatum = serializers.DateTimeField()
    indicatie_combi_dwangbevel = serializers.ChoiceField(choices=("J", "N", "O"))
    notatekst = serializers.CharField(max_length=2000, allow_null=True)
    omschrijving = serializers.CharField(max_length=100, allow_null=True)
    invorderingstatus = serializers.CharField()
    indicatie_bet_hern_bevel = serializers.ChoiceField(choices=("J", "N"))
    landcode = serializers.CharField(max_length="3", allow_null=True)
    kenteken = serializers.CharField(allow_null=True)
    bonnummer = serializers.CharField(allow_null=True)
    bedrag_opgelegd = serializers.DecimalField(max_digits=12, decimal_places=2)
    bedrag_open_post_incl_rente = serializers.DecimalField(
        max_digits=12, decimal_places=2
    )
    totaalbedrag_open_kosten = serializers.DecimalField(max_digits=12, decimal_places=2)
    bedrag_open_rente = serializers.DecimalField(max_digits=12, decimal_places=2)
    reden_opschorting = serializers.CharField(max_length=4000, allow_null=True)
    omschrijving_1 = serializers.CharField(max_length=4000, allow_null=True)
    omschrijving_2 = serializers.CharField(max_length=4000, allow_null=True)


class FineListSerializer(serializers.Serializer):
    items = FineSerializer(required=True, many=True)
    states_with_fines = FineSerializer(required=True, many=True)


class ResidentSerializer(serializers.Serializer):
    geboortedatum = serializers.DateTimeField(required=True)
    geslachtsaanduiding = serializers.ChoiceField(choices=("M", "V", "X"))
    geslachtsnaam = serializers.CharField(required=True)
    voorletters = serializers.CharField(required=True)
    voornamen = serializers.CharField(required=True)
    voorvoegsel_geslachtsnaam = serializers.CharField(required=False)
    datum_begin_relatie_verblijadres = serializers.DateTimeField(required=True)


class ResidentsSerializer(serializers.Serializer):
    items = ResidentSerializer(required=True, many=True)


class CaseTimelineSubjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = CaseTimelineSubject
        fields = "__all__"


class CaseTimelineReactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = CaseTimelineReaction
        fields = "__all__"


class CaseTimelineThreadSerializer(serializers.ModelSerializer):
    castetimelinereaction_set = CaseTimelineReactionSerializer(
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


class PermitCheckmarkSerializer(serializers.Serializer):
    has_b_and_b_permit = serializers.ChoiceField(choices=("True", "False", "UNKNOWN"))
    has_vacation_rental_permit = serializers.ChoiceField(
        choices=("True", "False", "UNKNOWN")
    )
