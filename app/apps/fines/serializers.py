from rest_framework import serializers


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
