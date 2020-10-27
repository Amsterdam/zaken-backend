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
