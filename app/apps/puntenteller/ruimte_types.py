from __future__ import annotations

from dataclasses import asdict, dataclass, field, fields
from decimal import Decimal

from apps.puntenteller.models import RuimteNaam

# Beleidsboek 2.2.1.2: een vertrek is minimaal 4,00 m².
MINIMALE_OPPERVLAKTE_VERTREK = Decimal("4.00")


@dataclass(frozen=True)
class BasisRuimte:
    naam: str
    ruimte_m2: Decimal
    verwarmd: bool = False
    aantal_adressen_met_toegang_en_gebruiksrecht: int = 1

    def as_dict(self) -> dict:
        data = asdict(self)
        for sleutel, waarde in list(data.items()):
            if isinstance(waarde, Decimal):
                data[sleutel] = str(waarde)
        return data


@dataclass(frozen=True)
class VertrekRuimte(BasisRuimte):
    gekoeld: bool = False
    wastafel: int = 0
    meerpersoons_wastafel: int = 0
    douche: int = 0
    bad: int = 0
    baddouche: int = 0


@dataclass(frozen=True)
class BadkamerRuimte(VertrekRuimte):
    toilet_hangend: int = 0
    toilet_normaal: int = 0
    bubbelfunctie_bad: int = 0
    volledige_afscheiding_douche: int = 0
    handdoekenradiator: int = 0
    kast_bij_wastafel: int = 0
    kastruimte: int = 0
    stopcontacten: int = 0
    eenhandsmengkraan: int = 0
    thermostatische_mengkraan: int = 0


@dataclass(frozen=True)
class KeukenRuimte(VertrekRuimte):
    aanrechtlengte_meters: Decimal | None = None
    inbouw_afzuiginstallatie: int = 0
    inbouw_kookplaat_inductie: int = 0
    inbouw_kookplaat_keramisch: int = 0
    inbouw_kookplaat_gas: int = 0
    inbouw_koelkast: int = 0
    inbouw_vrieskast: int = 0
    inbouw_oven_elektrisch: int = 0
    inbouw_oven_gas: int = 0
    inbouw_magnetron: int = 0
    inbouw_vaatwasmachine: int = 0
    extra_kastruimte: int = 0
    eenhandsmengkraan: int = 0
    thermostatische_mengkraan: int = 0
    kokendwaterfunctie: int = 0


@dataclass(frozen=True)
class OverigeRuimte(BasisRuimte):
    wastafel: int = 0
    meerpersoons_wastafel: int = 0
    douche: int = 0
    bad: int = 0
    baddouche: int = 0


@dataclass(frozen=True)
class ToiletRuimte(OverigeRuimte):
    toilet_staand: int = 0
    toilet_hangend: int = 0


@dataclass(frozen=True)
class VerkeersRuimte(BasisRuimte):
    pass


@dataclass(frozen=True)
class ZolderRuimte(OverigeRuimte):
    heeft_vaste_trap: bool = True
    aftrek_loopruimte_m2: Decimal | None = None


@dataclass(frozen=True)
class Buitenruimte:
    naam: str
    ruimte_m2: Decimal

    def as_dict(self) -> dict:
        data = asdict(self)
        for sleutel, waarde in list(data.items()):
            if isinstance(waarde, Decimal):
                data[sleutel] = str(waarde)
        return data


@dataclass(frozen=True)
class PriveBuitenruimte(Buitenruimte):
    pass


@dataclass(frozen=True)
class GemeenschappelijkeBuitenruimte(Buitenruimte):
    aantal_adressen_met_toegang_en_gebruiksrecht: int = 1


PARKEERRUIMTE_TYPES = (
    "gesloten_garage_bij_complex",
    "buiten_bij_complex_met_dak",
    "buiten_bij_complex_zonder_dak",
)


@dataclass(frozen=True)
class Parkeerruimte:
    naam: str
    type: str
    aantal_adressen_met_toegang_en_gebruiksrecht: int = 1
    laadpaal: bool = False

    def as_dict(self) -> dict:
        return asdict(self)


def maak_vertrek_ruimte(data: dict | None) -> VertrekRuimte:
    ruimte = data or {}
    naam = str(ruimte.get("naam") or "onbekende_ruimte")
    klasse = {
        RuimteNaam.BADKAMER: BadkamerRuimte,
        RuimteNaam.KEUKEN: KeukenRuimte,
    }.get(naam, VertrekRuimte)
    return _maak(klasse, ruimte, naam=naam)


def maak_overige_ruimte(data: dict | None) -> OverigeRuimte:
    ruimte = data or {}
    naam = str(ruimte.get("naam") or "onbekende_ruimte")
    if naam == RuimteNaam.TOILETRUIMTE:
        return _maak(
            ToiletRuimte,
            ruimte,
            naam=naam,
            toilet_staand=int(
                ruimte.get("toilet_staand") or ruimte.get("toilet_normaal") or 0
            ),
        )
    klasse = ZolderRuimte if naam == RuimteNaam.ZOLDER else OverigeRuimte
    return _maak(klasse, ruimte, naam=naam)


def maak_verkeersruimte(data: dict | None) -> VerkeersRuimte:
    ruimte = data or {}
    naam = str(ruimte.get("naam") or RuimteNaam.VERKEERSRUIMTE)
    return _maak(VerkeersRuimte, ruimte, naam=naam)


def maak_buitenruimte(data: dict | None) -> Buitenruimte:
    ruimte = data or {}
    naam = str(ruimte.get("naam") or "onbekende_buitenruimte")
    klasse = (
        GemeenschappelijkeBuitenruimte
        if naam == RuimteNaam.GEMEENSCHAPPELIJKE_BUITENRUIMTE
        else PriveBuitenruimte
    )
    return _maak(klasse, ruimte, naam=naam)


def maak_parkeerruimte(data: dict | None) -> Parkeerruimte:
    ruimte = data or {}
    return _maak(
        Parkeerruimte,
        ruimte,
        naam=str(ruimte.get("naam") or RuimteNaam.BUITENRUIMTE_PARKEERPLAATS),
        type=str(ruimte.get("type") or "onbekend"),
    )


def _maak(klasse, data: dict, **vaste_waarden):
    # Leest elk veld van de dataclass uit de invoer en zet het om naar het
    # veldtype. Ontbrekende of lege waarden krijgen de default van het veld.
    waarden = {}
    for veld in fields(klasse):
        if veld.name in vaste_waarden:
            continue
        invoer = data.get(veld.name)
        if veld.type == "int":
            waarden[veld.name] = int(invoer or veld.default)
        elif veld.type == "bool":
            waarden[veld.name] = bool(data.get(veld.name, veld.default))
        elif veld.type == "Decimal":
            waarden[veld.name] = Decimal(str(invoer or 0))
        elif veld.type == "Decimal | None":
            waarden[veld.name] = _decimaal_of_none(invoer)
        else:
            raise TypeError(f"Onbekend veldtype {veld.type} voor {veld.name}")
    return klasse(**waarden, **vaste_waarden)


def maak_parkeerruimten(data: dict | None) -> list[Parkeerruimte]:
    if not isinstance(data, dict):
        return []
    if "type" in data:
        return [maak_parkeerruimte(data)]

    # Telformaat uit de ParkeerruimteSerializer: per type een aantal plekken.
    # Laadpalen worden in volgorde over de plekken verdeeld.
    aantal_adressen = max(
        int(data.get("aantal_adressen_met_toegang_en_gebruiksrecht") or 0), 1
    )
    aantal_laadpalen = int(data.get("aantal_laadpalen") or 0)
    parkeerruimten = []
    for type_naam in PARKEERRUIMTE_TYPES:
        for _ in range(int(data.get(f"aantal_{type_naam}") or 0)):
            parkeerruimten.append(
                Parkeerruimte(
                    naam=str(data.get("naam") or RuimteNaam.BUITENRUIMTE_PARKEERPLAATS),
                    type=type_naam,
                    aantal_adressen_met_toegang_en_gebruiksrecht=aantal_adressen,
                    laadpaal=len(parkeerruimten) < aantal_laadpalen,
                )
            )
    return parkeerruimten


@dataclass(frozen=True)
class Ruimten:
    vertrekken: list[VertrekRuimte]
    overige_ruimten: list[OverigeRuimte]
    verkeersruimten: list[VerkeersRuimte]
    buitenruimten: list[Buitenruimte]
    parkeerruimten: list[Parkeerruimte]
    # Opgegeven als vertrek, maar gewaardeerd als overige ruimte.
    te_kleine_vertrekken: list[VertrekRuimte] = field(default_factory=list)

    @property
    def badkamers(self) -> list[BadkamerRuimte]:
        return [r for r in self.vertrekken if isinstance(r, BadkamerRuimte)]

    @property
    def keukens(self) -> list[KeukenRuimte]:
        return [r for r in self.vertrekken if isinstance(r, KeukenRuimte)]

    @property
    def toiletruimten(self) -> list[ToiletRuimte]:
        return [r for r in self.overige_ruimten if isinstance(r, ToiletRuimte)]


def maak_ruimten(gebruikersinvoer) -> Ruimten:
    vertrekken = [maak_vertrek_ruimte(r) for r in gebruikersinvoer.vertrekken or []]
    te_klein = [v for v in vertrekken if _te_klein_voor_vertrek(v)]
    return Ruimten(
        vertrekken=[v for v in vertrekken if not _te_klein_voor_vertrek(v)],
        overige_ruimten=[
            *(_als_overige_ruimte(v) for v in te_klein),
            *(maak_overige_ruimte(r) for r in gebruikersinvoer.overige_ruimten or []),
        ],
        verkeersruimten=[
            maak_verkeersruimte(r) for r in gebruikersinvoer.verkeersruimten or []
        ],
        buitenruimten=[
            maak_buitenruimte(r) for r in gebruikersinvoer.buitenruimten or []
        ],
        parkeerruimten=[
            parkeerruimte
            for r in gebruikersinvoer.parkeerruimten or []
            for parkeerruimte in maak_parkeerruimten(r)
        ],
        te_kleine_vertrekken=te_klein,
    )


def _te_klein_voor_vertrek(vertrek: VertrekRuimte) -> bool:
    # Beleidsboek 2.2.1: een keuken of badkamer is altijd een vertrek. Een
    # ander vertrek kleiner dan 4 m² voldoet niet en is een overige ruimte
    # (2.2.2.2). Zonder opgegeven oppervlakte blijft het een vertrek.
    if isinstance(vertrek, (BadkamerRuimte, KeukenRuimte)):
        return False
    return 0 < vertrek.ruimte_m2 < MINIMALE_OPPERVLAKTE_VERTREK


def _als_overige_ruimte(vertrek: VertrekRuimte) -> OverigeRuimte:
    return OverigeRuimte(
        naam=vertrek.naam,
        ruimte_m2=vertrek.ruimte_m2,
        verwarmd=vertrek.verwarmd,
        aantal_adressen_met_toegang_en_gebruiksrecht=(
            vertrek.aantal_adressen_met_toegang_en_gebruiksrecht
        ),
        wastafel=vertrek.wastafel,
        meerpersoons_wastafel=vertrek.meerpersoons_wastafel,
        douche=vertrek.douche,
        bad=vertrek.bad,
        baddouche=vertrek.baddouche,
    )


def _decimaal_of_none(waarde) -> Decimal | None:
    if waarde is None or waarde == "":
        return None
    return Decimal(str(waarde))
