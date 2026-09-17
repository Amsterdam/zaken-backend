from apps.puntenteller.models import Gebruikersinvoer, RuimteNaam
from apps.puntenteller.ruimte_types import (
    maak_overige_ruimte,
    maak_verkeersruimte,
    maak_vertrek_ruimte,
)
from drf_spectacular.utils import PolymorphicProxySerializer, extend_schema_field
from rest_framework import serializers


def _ruimte_keuzes(*ruimtenamen):
    return [(ruimtenaam, ruimtenaam.label) for ruimtenaam in ruimtenamen]


class BasisRuimteSerializer(serializers.Serializer):
    naam = serializers.ChoiceField(choices=RuimteNaam.choices)
    ruimte_m2 = serializers.DecimalField(max_digits=8, decimal_places=2)
    verwarmd = serializers.BooleanField(required=False, default=False)


class BasisVertrekSerializer(BasisRuimteSerializer):
    gekoeld = serializers.BooleanField(required=False, default=False)


class StandaardVertrekSerializer(BasisVertrekSerializer):
    naam = serializers.ChoiceField(
        choices=_ruimte_keuzes(
            RuimteNaam.WOONKAMER,
            RuimteNaam.SLAAPKAMER,
            RuimteNaam.TOILETRUIMTE,
            RuimteNaam.WASRUIMTE_BIJKEUKEN,
        )
    )


class BadkamerRuimteSerializer(BasisVertrekSerializer):
    naam = serializers.ChoiceField(choices=_ruimte_keuzes(RuimteNaam.BADKAMER))
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


class KeukenRuimteSerializer(BasisVertrekSerializer):
    naam = serializers.ChoiceField(choices=_ruimte_keuzes(RuimteNaam.KEUKEN))
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


class BasisOverigeRuimteSerializer(BasisRuimteSerializer):
    pass


class StandaardOverigeRuimteSerializer(BasisOverigeRuimteSerializer):
    naam = serializers.ChoiceField(
        choices=_ruimte_keuzes(
            RuimteNaam.BERGING,
            RuimteNaam.KELDER,
            RuimteNaam.PRIVE_PARKEERRUIMTE,
        )
    )


class ZolderRuimteSerializer(BasisOverigeRuimteSerializer):
    naam = serializers.ChoiceField(choices=_ruimte_keuzes(RuimteNaam.ZOLDER))
    heeft_vaste_trap = serializers.BooleanField(required=False, default=True)
    aftrek_loopruimte_m2 = serializers.DecimalField(
        max_digits=8, decimal_places=2, required=False, allow_null=True
    )


class VerkeersRuimteSerializer(BasisRuimteSerializer):
    naam = serializers.ChoiceField(choices=_ruimte_keuzes(RuimteNaam.VERKEERSRUIMTE))


class PolymorfeRuimteSerializer(serializers.Serializer):
    serializer_mapping = {}

    def to_internal_value(self, data):
        serializer = self._maak_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        return serializer.validated_data

    def to_representation(self, instance):
        serializer = self._maak_serializer(instance=instance)
        return serializer.data

    def _maak_serializer(self, data=None, instance=None):
        bron = data if data is not None else instance
        serializer_class = self._serializer_klasse_voor_bron(bron)
        kwargs = {"context": self.context}
        if data is not None:
            kwargs["data"] = data
        if instance is not None:
            kwargs["instance"] = instance
        return serializer_class(**kwargs)

    def _serializer_klasse_voor_bron(self, bron):
        if not isinstance(bron, dict):
            raise serializers.ValidationError("Ruimte moet een object zijn.")

        naam = bron.get("naam")
        serializer_class = self.serializer_mapping.get(naam)
        if serializer_class:
            return serializer_class

        raise serializers.ValidationError(
            {"naam": f"Ongeldig ruimtetype voor dit veld: {naam}"}
        )


class VertrekRuimteInvoerSerializer(PolymorfeRuimteSerializer):
    serializer_mapping = {
        RuimteNaam.WOONKAMER: StandaardVertrekSerializer,
        RuimteNaam.SLAAPKAMER: StandaardVertrekSerializer,
        RuimteNaam.TOILETRUIMTE: StandaardVertrekSerializer,
        RuimteNaam.WASRUIMTE_BIJKEUKEN: StandaardVertrekSerializer,
        RuimteNaam.BADKAMER: BadkamerRuimteSerializer,
        RuimteNaam.KEUKEN: KeukenRuimteSerializer,
    }


class OverigeRuimteInvoerSerializer(PolymorfeRuimteSerializer):
    serializer_mapping = {
        RuimteNaam.BERGING: StandaardOverigeRuimteSerializer,
        RuimteNaam.KELDER: StandaardOverigeRuimteSerializer,
        RuimteNaam.PRIVE_PARKEERRUIMTE: StandaardOverigeRuimteSerializer,
        RuimteNaam.ZOLDER: ZolderRuimteSerializer,
    }


class VerkeersRuimteInvoerSerializer(PolymorfeRuimteSerializer):
    serializer_mapping = {RuimteNaam.VERKEERSRUIMTE: VerkeersRuimteSerializer}


@extend_schema_field(
    PolymorphicProxySerializer(
        component_name="VertrekRuimteInput",
        serializers=[
            StandaardVertrekSerializer,
            BadkamerRuimteSerializer,
            KeukenRuimteSerializer,
        ],
        resource_type_field_name="naam",
        many=True,
    )
)
class VertrekRuimteSchemaField(serializers.JSONField):
    pass


@extend_schema_field(
    PolymorphicProxySerializer(
        component_name="OverigeRuimteInput",
        serializers=[StandaardOverigeRuimteSerializer, ZolderRuimteSerializer],
        resource_type_field_name="naam",
        many=True,
    )
)
class OverigeRuimteSchemaField(serializers.JSONField):
    pass


@extend_schema_field(
    PolymorphicProxySerializer(
        component_name="VerkeersRuimteInput",
        serializers=[VerkeersRuimteSerializer],
        resource_type_field_name="naam",
        many=True,
    )
)
class VerkeersRuimteSchemaField(serializers.JSONField):
    pass


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
    vertrekken = VertrekRuimteInvoerSerializer(many=True, required=False)
    overige_ruimten = OverigeRuimteInvoerSerializer(many=True, required=False)
    verkeersruimten = VerkeersRuimteInvoerSerializer(many=True, required=False)

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


class GebruikersinvoerRequestSerializer(serializers.ModelSerializer):
    vertrekken = VertrekRuimteSchemaField(required=False)
    overige_ruimten = OverigeRuimteSchemaField(required=False)
    verkeersruimten = VerkeersRuimteSchemaField(required=False)

    class Meta:
        model = Gebruikersinvoer
        exclude = ("adres", "gebruiker")
