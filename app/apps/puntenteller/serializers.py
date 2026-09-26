from decimal import Decimal, InvalidOperation

from apps.puntenteller.models import Gebruikersinvoer, RuimteNaam
from apps.puntenteller.ruimte_types import (
    maak_buitenruimte,
    maak_overige_ruimte,
    maak_parkeerruimte,
    maak_verkeersruimte,
    maak_vertrek_ruimte,
)
from drf_spectacular.utils import PolymorphicProxySerializer, extend_schema_field
from rest_framework import serializers

ENERGIE_MODEL_VELDEN = (
    "energielabel_klasse",
    "energie_index",
    "heeft_energieprestatievergoeding",
)


def _ruimte_keuzes(*ruimtenamen):
    return [(ruimtenaam, ruimtenaam.label) for ruimtenaam in ruimtenamen]


class EnergieSerializer(serializers.Serializer):
    type = serializers.ChoiceField(choices=("label", "index", "bouwjaar"))
    waarde = serializers.CharField(required=False, allow_null=True, allow_blank=False)
    heeft_energieprestatievergoeding = serializers.BooleanField(
        required=False, default=False
    )

    def validate(self, attrs):
        energie_type = attrs["type"]
        waarde = attrs.get("waarde")
        if energie_type in {"label", "index"} and waarde in (None, ""):
            raise serializers.ValidationError({"waarde": "Dit veld is verplicht."})

        if energie_type == "index" and waarde not in (None, ""):
            try:
                attrs["waarde"] = Decimal(str(waarde))
            except (InvalidOperation, TypeError, ValueError):
                raise serializers.ValidationError(
                    {"waarde": "Vul een geldige energie-index in."}
                )

        if energie_type == "bouwjaar":
            attrs["waarde"] = None
        return attrs


class BasisRuimteSerializer(serializers.Serializer):
    naam = serializers.ChoiceField(choices=RuimteNaam.choices)
    ruimte_m2 = serializers.DecimalField(max_digits=8, decimal_places=2)
    verwarmd = serializers.BooleanField(required=False, default=False)
    aantal_adressen_met_toegang_en_gebruiksrecht = serializers.IntegerField(
        required=False, default=1, min_value=1
    )


class BasisVertrekSerializer(BasisRuimteSerializer):
    gekoeld = serializers.BooleanField(required=False, default=False)
    wastafel = serializers.IntegerField(required=False, default=0)
    meerpersoons_wastafel = serializers.IntegerField(required=False, default=0)
    douche = serializers.IntegerField(required=False, default=0)
    bad = serializers.IntegerField(required=False, default=0)
    baddouche = serializers.IntegerField(required=False, default=0)


class StandaardVertrekSerializer(BasisVertrekSerializer):
    naam = serializers.ChoiceField(
        choices=_ruimte_keuzes(
            RuimteNaam.WOONKAMER,
            RuimteNaam.SLAAPKAMER,
            RuimteNaam.WASRUIMTE_BIJKEUKEN,
        )
    )


class BadkamerRuimteSerializer(BasisVertrekSerializer):
    naam = serializers.ChoiceField(choices=_ruimte_keuzes(RuimteNaam.BADKAMER))
    toilet_hangend = serializers.IntegerField(required=False, default=0)
    toilet_normaal = serializers.IntegerField(required=False, default=0)
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
    wastafel = serializers.IntegerField(required=False, default=0)
    meerpersoons_wastafel = serializers.IntegerField(required=False, default=0)
    douche = serializers.IntegerField(required=False, default=0)
    bad = serializers.IntegerField(required=False, default=0)
    baddouche = serializers.IntegerField(required=False, default=0)


class ToiletRuimteSerializer(BasisOverigeRuimteSerializer):
    naam = serializers.ChoiceField(choices=_ruimte_keuzes(RuimteNaam.TOILETRUIMTE))
    toilet_staand = serializers.IntegerField(required=False, default=0)
    toilet_hangend = serializers.IntegerField(required=False, default=0)


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


class BuitenruimteSerializer(serializers.Serializer):
    naam = serializers.ChoiceField(
        choices=_ruimte_keuzes(
            RuimteNaam.PRIVE_BUITENRUIMTE,
            RuimteNaam.GEMEENSCHAPPELIJKE_BUITENRUIMTE,
        )
    )
    ruimte_m2 = serializers.DecimalField(max_digits=8, decimal_places=2)
    aantal_adressen_met_toegang_en_gebruiksrecht = serializers.IntegerField(
        required=False, default=1, min_value=1
    )

    def validate(self, attrs):
        if attrs["naam"] == RuimteNaam.PRIVE_BUITENRUIMTE:
            attrs.pop("aantal_adressen_met_toegang_en_gebruiksrecht", None)
        return attrs


class ParkeerruimteSerializer(serializers.Serializer):
    naam = serializers.ChoiceField(
        choices=_ruimte_keuzes(RuimteNaam.BUITENRUIMTE_PARKEERPLAATS)
    )
    type = serializers.ChoiceField(
        choices=(
            ("gesloten_garage_bij_complex", "Gesloten garage bij complex"),
            ("buiten_bij_complex_met_dak", "Buiten bij complex met dak"),
            ("buiten_bij_complex_zonder_dak", "Buiten bij complex zonder dak"),
        )
    )
    aantal_adressen_met_toegang_en_gebruiksrecht = serializers.IntegerField(
        required=False, default=1, min_value=1
    )
    laadpaal = serializers.BooleanField(required=False, default=False)


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
        RuimteNaam.WASRUIMTE_BIJKEUKEN: StandaardVertrekSerializer,
        RuimteNaam.BADKAMER: BadkamerRuimteSerializer,
        RuimteNaam.KEUKEN: KeukenRuimteSerializer,
    }


class OverigeRuimteInvoerSerializer(PolymorfeRuimteSerializer):
    serializer_mapping = {
        RuimteNaam.BERGING: StandaardOverigeRuimteSerializer,
        RuimteNaam.KELDER: StandaardOverigeRuimteSerializer,
        RuimteNaam.PRIVE_PARKEERRUIMTE: StandaardOverigeRuimteSerializer,
        RuimteNaam.TOILETRUIMTE: ToiletRuimteSerializer,
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
        serializers=[
            StandaardOverigeRuimteSerializer,
            ToiletRuimteSerializer,
            ZolderRuimteSerializer,
        ],
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


@extend_schema_field(
    PolymorphicProxySerializer(
        component_name="VertrekRuimteResponse",
        serializers=[
            StandaardVertrekSerializer,
            BadkamerRuimteSerializer,
            KeukenRuimteSerializer,
        ],
        resource_type_field_name="naam",
        many=True,
    )
)
class VertrekRuimteResponseSchemaField(serializers.JSONField):
    pass


@extend_schema_field(
    PolymorphicProxySerializer(
        component_name="OverigeRuimteResponse",
        serializers=[
            StandaardOverigeRuimteSerializer,
            ToiletRuimteSerializer,
            ZolderRuimteSerializer,
        ],
        resource_type_field_name="naam",
        many=True,
    )
)
class OverigeRuimteResponseSchemaField(serializers.JSONField):
    pass


@extend_schema_field(
    PolymorphicProxySerializer(
        component_name="VerkeersRuimteResponse",
        serializers=[VerkeersRuimteSerializer],
        resource_type_field_name="naam",
        many=True,
    )
)
class VerkeersRuimteResponseSchemaField(serializers.JSONField):
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
    energie = serializers.DictField(allow_null=True)


class EnergieSerializerMixin:
    def validate(self, attrs):
        return super().validate(attrs)

    def create(self, validated_data):
        validated_data = self._normaliseer_energie_data(validated_data)
        return super().create(validated_data)

    def update(self, instance, validated_data):
        validated_data = self._normaliseer_energie_data(
            validated_data, instance=instance
        )
        return super().update(instance, validated_data)

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["energie"] = self._energie_representatie(instance)
        return data

    def _normaliseer_energie_data(self, validated_data, instance=None):
        is_eengezinswoning = validated_data.get(
            "is_eengezinswoning",
            getattr(instance, "is_eengezinswoning", None) if instance else None,
        )
        energie = validated_data.pop("energie", serializers.empty)
        if energie is serializers.empty and hasattr(self, "initial_data"):
            ruwe_energie = self.initial_data.get("energie", serializers.empty)
            if ruwe_energie is not serializers.empty:
                energie_serializer = EnergieSerializer(data=ruwe_energie)
                energie_serializer.is_valid(raise_exception=True)
                energie = energie_serializer.validated_data
        if energie is serializers.empty:
            return validated_data

        for veldnaam, waarde in self._energie_model_defaults().items():
            validated_data[veldnaam] = waarde

        validated_data.update(
            {
                "is_eengezinswoning": is_eengezinswoning,
                "heeft_energieprestatievergoeding": energie.get(
                    "heeft_energieprestatievergoeding", False
                ),
            }
        )

        if energie["type"] == "label":
            validated_data["energielabel_klasse"] = energie.get("waarde")
        elif energie["type"] == "index":
            validated_data["energie_index"] = energie.get("waarde")

        return validated_data

    def _energie_model_defaults(self):
        return {
            "energielabel_klasse": None,
            "energie_index": None,
            "is_eengezinswoning": None,
            "heeft_energieprestatievergoeding": False,
        }

    def _energie_representatie(self, instance):
        if getattr(instance, "is_eengezinswoning", None) is None:
            return None

        energie_type = "bouwjaar"
        if instance.energielabel_klasse:
            energie_type = "label"
        elif instance.energie_index is not None:
            energie_type = "index"

        data = {
            "type": energie_type,
            "waarde": None,
            "heeft_energieprestatievergoeding": instance.heeft_energieprestatievergoeding,
        }
        if energie_type == "label":
            data["waarde"] = instance.energielabel_klasse
        if energie_type == "index":
            data["waarde"] = instance.energie_index
        return data


class PuntentellerResultaatSerializer(serializers.Serializer):
    rubrieken = serializers.DictField(child=serializers.FloatField())
    energieprestatie_berekening = serializers.JSONField()
    totaal_punten_bruto = serializers.FloatField()
    correcties = serializers.DictField(child=serializers.JSONField(allow_null=True))
    totaal_punten_na_caps = serializers.FloatField()


class GebruikersinvoerSerializer(EnergieSerializerMixin, serializers.ModelSerializer):
    energie = EnergieSerializer(required=False)
    buitenruimten = BuitenruimteSerializer(many=True, required=False)
    parkeerruimten = ParkeerruimteSerializer(many=True, required=False)
    is_eengezinswoning = serializers.BooleanField(required=False, allow_null=True)
    zorgwoning = serializers.BooleanField(required=False, default=False)
    nieuwbouw = serializers.BooleanField(required=False, default=False)
    bijzondere_voorziening_intercom_met_beeld = serializers.BooleanField(
        required=False, default=False
    )
    bijzondere_voorziening_laadpalen = serializers.IntegerField(
        required=False, default=0, min_value=0
    )
    vertrekken = VertrekRuimteInvoerSerializer(many=True, required=False)
    overige_ruimten = OverigeRuimteInvoerSerializer(many=True, required=False)
    verkeersruimten = VerkeersRuimteInvoerSerializer(many=True, required=False)

    class Meta:
        model = Gebruikersinvoer
        exclude = ENERGIE_MODEL_VELDEN
        read_only_fields = ("gebruiker",)
        extra_kwargs = {"adres": {"required": False}}

    def create(self, validated_data):
        validated_data = self._normaliseer_energie_data(validated_data)
        validated_data["vertrekken"] = self._normaliseer_vertrekken(
            validated_data.pop("vertrekken", [])
        )
        validated_data["overige_ruimten"] = self._normaliseer_overige_ruimten(
            validated_data.pop("overige_ruimten", [])
        )
        validated_data["verkeersruimten"] = self._normaliseer_verkeersruimten(
            validated_data.pop("verkeersruimten", [])
        )
        validated_data["buitenruimten"] = self._normaliseer_buitenruimten(
            validated_data.pop("buitenruimten", [])
        )
        validated_data["parkeerruimten"] = self._normaliseer_parkeerruimten(
            validated_data.pop("parkeerruimten", [])
        )
        return Gebruikersinvoer.objects.create(**validated_data)

    def update(self, instance, validated_data):
        validated_data = self._normaliseer_energie_data(validated_data, instance)
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
        if "buitenruimten" in validated_data:
            instance.buitenruimten = self._normaliseer_buitenruimten(
                validated_data.pop("buitenruimten")
            )
        if "parkeerruimten" in validated_data:
            instance.parkeerruimten = self._normaliseer_parkeerruimten(
                validated_data.pop("parkeerruimten")
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

    def _normaliseer_buitenruimten(self, ruimten):
        return [maak_buitenruimte(ruimte).as_dict() for ruimte in ruimten]

    def _normaliseer_parkeerruimten(self, ruimten):
        return [maak_parkeerruimte(ruimte).as_dict() for ruimte in ruimten]

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


class GebruikersinvoerRequestSerializer(
    EnergieSerializerMixin, serializers.ModelSerializer
):
    energie = EnergieSerializer(required=False)
    buitenruimten = BuitenruimteSerializer(many=True, required=False)
    parkeerruimten = ParkeerruimteSerializer(many=True, required=False)
    is_eengezinswoning = serializers.BooleanField(required=False, allow_null=True)
    zorgwoning = serializers.BooleanField(required=False, default=False)
    nieuwbouw = serializers.BooleanField(required=False, default=False)
    bijzondere_voorziening_intercom_met_beeld = serializers.BooleanField(
        required=False, default=False
    )
    bijzondere_voorziening_laadpalen = serializers.IntegerField(
        required=False, default=0, min_value=0
    )
    vertrekken = VertrekRuimteSchemaField(required=False)
    overige_ruimten = OverigeRuimteSchemaField(required=False)
    verkeersruimten = VerkeersRuimteSchemaField(required=False)

    class Meta:
        model = Gebruikersinvoer
        exclude = ("adres", "gebruiker", *ENERGIE_MODEL_VELDEN)


class GebruikersinvoerResponseSerializer(
    EnergieSerializerMixin, serializers.ModelSerializer
):
    energie = EnergieSerializer(required=False)
    buitenruimten = BuitenruimteSerializer(many=True, required=False)
    parkeerruimten = ParkeerruimteSerializer(many=True, required=False)
    is_eengezinswoning = serializers.BooleanField(required=False, allow_null=True)
    zorgwoning = serializers.BooleanField(required=False, default=False)
    nieuwbouw = serializers.BooleanField(required=False, default=False)
    bijzondere_voorziening_intercom_met_beeld = serializers.BooleanField(
        required=False, default=False
    )
    bijzondere_voorziening_laadpalen = serializers.IntegerField(
        required=False, default=0, min_value=0
    )
    vertrekken = VertrekRuimteResponseSchemaField(required=False)
    overige_ruimten = OverigeRuimteResponseSchemaField(required=False)
    verkeersruimten = VerkeersRuimteResponseSchemaField(required=False)
    punten = serializers.FloatField()
    punten_resultaat = PuntentellerResultaatSerializer()

    class Meta:
        model = Gebruikersinvoer
        exclude = ENERGIE_MODEL_VELDEN


class GebruikersinvoerCreateResponseSerializer(PuntentellerResultaatSerializer):
    pass
