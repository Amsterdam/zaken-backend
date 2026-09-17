from apps.puntenteller.models import Gebruikersinvoer, RuimteNaam
from apps.puntenteller.ruimte_types import (
    maak_overige_ruimte,
    maak_verkeersruimte,
    maak_vertrek_ruimte,
)
from rest_framework import serializers


class RuimteSerializer(serializers.Serializer):
    naam = serializers.ChoiceField(choices=RuimteNaam.choices)
    ruimte_m2 = serializers.DecimalField(max_digits=8, decimal_places=2)
    verwarmd = serializers.BooleanField(required=False, default=False)
    gekoeld = serializers.BooleanField(required=False, default=False)
    toilet_hangend = serializers.IntegerField(required=False, default=0)
    toilet_normaal = serializers.IntegerField(required=False, default=0)
    wastafel = serializers.IntegerField(required=False, default=0)
    meerpersoons_wastafel = serializers.IntegerField(required=False, default=0)
    douche = serializers.IntegerField(required=False, default=0)
    bad = serializers.IntegerField(required=False, default=0)
    baddouche = serializers.IntegerField(required=False, default=0)
    bubbelfunctie_bad = serializers.IntegerField(required=False, default=0)
    volledige_afscheiding_douche = serializers.IntegerField(required=False, default=0)
    handdoekenradiator = serializers.IntegerField(required=False, default=0)
    kast_bij_wastafel = serializers.IntegerField(required=False, default=0)
    kastruimte = serializers.IntegerField(required=False, default=0)
    stopcontacten = serializers.IntegerField(required=False, default=0)
    eenhandsmengkraan = serializers.IntegerField(required=False, default=0)
    thermostatische_mengkraan = serializers.IntegerField(required=False, default=0)
    vloer_begaanbaar = serializers.BooleanField(required=False, default=True)
    heeft_vaste_trap = serializers.BooleanField(required=False, default=True)
    aftrek_loopruimte_m2 = serializers.DecimalField(
        max_digits=8, decimal_places=2, required=False, allow_null=True
    )
    aanrechtlengte_meters = serializers.DecimalField(
        max_digits=8, decimal_places=2, required=False, allow_null=True
    )
    inbouw_afzuiginstallatie = serializers.IntegerField(required=False, default=0)
    inbouw_kookplaat_inductie = serializers.IntegerField(required=False, default=0)
    inbouw_kookplaat_keramisch = serializers.IntegerField(required=False, default=0)
    inbouw_kookplaat_gas = serializers.IntegerField(required=False, default=0)
    inbouw_koelkast = serializers.IntegerField(required=False, default=0)
    inbouw_vrieskast = serializers.IntegerField(required=False, default=0)
    inbouw_oven_elektrisch = serializers.IntegerField(required=False, default=0)
    inbouw_oven_gas = serializers.IntegerField(required=False, default=0)
    inbouw_magnetron = serializers.IntegerField(required=False, default=0)
    inbouw_vaatwasmachine = serializers.IntegerField(required=False, default=0)
    extra_kastruimte = serializers.IntegerField(required=False, default=0)
    eenhandsmengkraan = serializers.IntegerField(required=False, default=0)
    thermostatische_mengkraan = serializers.IntegerField(required=False, default=0)
    kokendwaterfunctie = serializers.IntegerField(required=False, default=0)


class WozWaardeSerializer(serializers.Serializer):
    peildatum = serializers.DateField()
    vastgestelde_waarde = serializers.IntegerField()


class GebouwDataSerializer(serializers.Serializer):
    straat = serializers.CharField(allow_null=True)
    huisnummer = serializers.CharField(allow_null=True)
    bouwjaar = serializers.IntegerField(allow_null=True)
    gebruiksoppervlakte = serializers.IntegerField(allow_null=True)
    woz_waarden = WozWaardeSerializer(many=True, allow_null=True)
    wozobjectnummer = serializers.IntegerField(allow_null=True)
    energielabel = serializers.CharField(allow_null=True)


class GebruikersinvoerSerializer(serializers.ModelSerializer):
    vertrekken = RuimteSerializer(many=True, required=False)
    overige_ruimten = RuimteSerializer(many=True, required=False)
    verkeersruimten = RuimteSerializer(many=True, required=False)

    class Meta:
        model = Gebruikersinvoer
        fields = "__all__"
        read_only_fields = ("gebruiker",)

    def create(self, validated_data):
        validated_data["vertrekken"] = self._normaliseer_vertrekken(
            validated_data.pop("vertrekken", [])
        )
        validated_data["overige_ruimten"] = self._normaliseer_overige_ruimten(
            validated_data.pop("overige_ruimten", [])
        )
        validated_data["verkeersruimten"] = self._normaliseer_verkeersruimten(
            validated_data.pop("verkeersruimten", [])
        )
        return Gebruikersinvoer.objects.create(**validated_data)

    def update(self, instance, validated_data):
        if "vertrekken" in validated_data:
            instance.vertrekken = self._normaliseer_vertrekken(
                validated_data.pop("vertrekken")
            )
        if "overige_ruimten" in validated_data:
            instance.overige_ruimten = self._normaliseer_overige_ruimten(
                validated_data.pop("overige_ruimten")
            )
        if "verkeersruimten" in validated_data:
            instance.verkeersruimten = self._normaliseer_verkeersruimten(
                validated_data.pop("verkeersruimten")
            )

        for attribuut, waarde in validated_data.items():
            setattr(instance, attribuut, waarde)

        instance.save()
        return instance

    def _normaliseer_vertrekken(self, ruimten):
        return [maak_vertrek_ruimte(ruimte).as_dict() for ruimte in ruimten]

    def _normaliseer_overige_ruimten(self, ruimten):
        self._valideer_geen_verkoeling(ruimten, "overige_ruimten")
        return [maak_overige_ruimte(ruimte).as_dict() for ruimte in ruimten]

    def _normaliseer_verkeersruimten(self, ruimten):
        self._valideer_geen_verkoeling(ruimten, "verkeersruimten")
        return [maak_verkeersruimte(ruimte).as_dict() for ruimte in ruimten]

    def _valideer_geen_verkoeling(self, ruimten, veldnaam):
        for index, ruimte in enumerate(ruimten):
            if ruimte.get("gekoeld"):
                raise serializers.ValidationError(
                    {
                        veldnaam: {
                            index: "Verkoeling mag alleen op een vertrek worden ingevuld."
                        }
                    }
                )
