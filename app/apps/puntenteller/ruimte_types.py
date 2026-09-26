from __future__ import annotations

from dataclasses import asdict, dataclass
from decimal import Decimal

from apps.puntenteller.models import RuimteNaam


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
    ruimte_m2 = Decimal(str(ruimte.get("ruimte_m2") or 0))
    verwarmd = bool(ruimte.get("verwarmd", False))
    gekoeld = bool(ruimte.get("gekoeld", False))
    aantal_adressen_met_toegang_en_gebruiksrecht = int(
        ruimte.get("aantal_adressen_met_toegang_en_gebruiksrecht") or 1
    )
    if naam == RuimteNaam.BADKAMER:
        return BadkamerRuimte(
            naam=naam,
            ruimte_m2=ruimte_m2,
            verwarmd=verwarmd,
            aantal_adressen_met_toegang_en_gebruiksrecht=(
                aantal_adressen_met_toegang_en_gebruiksrecht
            ),
            gekoeld=gekoeld,
            toilet_hangend=int(ruimte.get("toilet_hangend") or 0),
            toilet_normaal=int(ruimte.get("toilet_normaal") or 0),
            wastafel=int(ruimte.get("wastafel") or 0),
            meerpersoons_wastafel=int(ruimte.get("meerpersoons_wastafel") or 0),
            douche=int(ruimte.get("douche") or 0),
            bad=int(ruimte.get("bad") or 0),
            baddouche=int(ruimte.get("baddouche") or 0),
            bubbelfunctie_bad=int(ruimte.get("bubbelfunctie_bad") or 0),
            volledige_afscheiding_douche=int(
                ruimte.get("volledige_afscheiding_douche") or 0
            ),
            handdoekenradiator=int(ruimte.get("handdoekenradiator") or 0),
            kast_bij_wastafel=int(ruimte.get("kast_bij_wastafel") or 0),
            kastruimte=int(ruimte.get("kastruimte") or 0),
            stopcontacten=int(ruimte.get("stopcontacten") or 0),
            eenhandsmengkraan=int(ruimte.get("eenhandsmengkraan") or 0),
            thermostatische_mengkraan=int(ruimte.get("thermostatische_mengkraan") or 0),
        )
    if naam == RuimteNaam.KEUKEN:
        return KeukenRuimte(
            naam=naam,
            ruimte_m2=ruimte_m2,
            verwarmd=verwarmd,
            aantal_adressen_met_toegang_en_gebruiksrecht=(
                aantal_adressen_met_toegang_en_gebruiksrecht
            ),
            gekoeld=gekoeld,
            wastafel=int(ruimte.get("wastafel") or 0),
            meerpersoons_wastafel=int(ruimte.get("meerpersoons_wastafel") or 0),
            douche=int(ruimte.get("douche") or 0),
            bad=int(ruimte.get("bad") or 0),
            baddouche=int(ruimte.get("baddouche") or 0),
            aanrechtlengte_meters=_decimaal_of_none(
                ruimte.get("aanrechtlengte_meters")
            ),
            inbouw_afzuiginstallatie=int(ruimte.get("inbouw_afzuiginstallatie") or 0),
            inbouw_kookplaat_inductie=int(ruimte.get("inbouw_kookplaat_inductie") or 0),
            inbouw_kookplaat_keramisch=int(
                ruimte.get("inbouw_kookplaat_keramisch") or 0
            ),
            inbouw_kookplaat_gas=int(ruimte.get("inbouw_kookplaat_gas") or 0),
            inbouw_koelkast=int(ruimte.get("inbouw_koelkast") or 0),
            inbouw_vrieskast=int(ruimte.get("inbouw_vrieskast") or 0),
            inbouw_oven_elektrisch=int(ruimte.get("inbouw_oven_elektrisch") or 0),
            inbouw_oven_gas=int(ruimte.get("inbouw_oven_gas") or 0),
            inbouw_magnetron=int(ruimte.get("inbouw_magnetron") or 0),
            inbouw_vaatwasmachine=int(ruimte.get("inbouw_vaatwasmachine") or 0),
            extra_kastruimte=int(ruimte.get("extra_kastruimte") or 0),
            eenhandsmengkraan=int(ruimte.get("eenhandsmengkraan") or 0),
            thermostatische_mengkraan=int(ruimte.get("thermostatische_mengkraan") or 0),
            kokendwaterfunctie=int(ruimte.get("kokendwaterfunctie") or 0),
        )
    return VertrekRuimte(
        naam=naam,
        ruimte_m2=ruimte_m2,
        verwarmd=verwarmd,
        aantal_adressen_met_toegang_en_gebruiksrecht=(
            aantal_adressen_met_toegang_en_gebruiksrecht
        ),
        gekoeld=gekoeld,
        wastafel=int(ruimte.get("wastafel") or 0),
        meerpersoons_wastafel=int(ruimte.get("meerpersoons_wastafel") or 0),
        douche=int(ruimte.get("douche") or 0),
        bad=int(ruimte.get("bad") or 0),
        baddouche=int(ruimte.get("baddouche") or 0),
    )


def maak_overige_ruimte(data: dict | None) -> OverigeRuimte:
    ruimte = data or {}
    naam = str(ruimte.get("naam") or "onbekende_ruimte")
    ruimte_m2 = Decimal(str(ruimte.get("ruimte_m2") or 0))
    verwarmd = bool(ruimte.get("verwarmd", False))
    aantal_adressen_met_toegang_en_gebruiksrecht = int(
        ruimte.get("aantal_adressen_met_toegang_en_gebruiksrecht") or 1
    )
    if naam == RuimteNaam.TOILETRUIMTE:
        return ToiletRuimte(
            naam=naam,
            ruimte_m2=ruimte_m2,
            verwarmd=verwarmd,
            aantal_adressen_met_toegang_en_gebruiksrecht=(
                aantal_adressen_met_toegang_en_gebruiksrecht
            ),
            toilet_staand=int(
                ruimte.get("toilet_staand") or ruimte.get("toilet_normaal") or 0
            ),
            toilet_hangend=int(ruimte.get("toilet_hangend") or 0),
            wastafel=int(ruimte.get("wastafel") or 0),
            meerpersoons_wastafel=int(ruimte.get("meerpersoons_wastafel") or 0),
        )
    if naam == RuimteNaam.ZOLDER:
        return ZolderRuimte(
            naam=naam,
            ruimte_m2=ruimte_m2,
            verwarmd=verwarmd,
            aantal_adressen_met_toegang_en_gebruiksrecht=(
                aantal_adressen_met_toegang_en_gebruiksrecht
            ),
            wastafel=int(ruimte.get("wastafel") or 0),
            meerpersoons_wastafel=int(ruimte.get("meerpersoons_wastafel") or 0),
            douche=int(ruimte.get("douche") or 0),
            bad=int(ruimte.get("bad") or 0),
            baddouche=int(ruimte.get("baddouche") or 0),
            heeft_vaste_trap=bool(ruimte.get("heeft_vaste_trap", True)),
            aftrek_loopruimte_m2=_decimaal_of_none(ruimte.get("aftrek_loopruimte_m2")),
        )
    return OverigeRuimte(
        naam=naam,
        ruimte_m2=ruimte_m2,
        verwarmd=verwarmd,
        aantal_adressen_met_toegang_en_gebruiksrecht=(
            aantal_adressen_met_toegang_en_gebruiksrecht
        ),
        wastafel=int(ruimte.get("wastafel") or 0),
        meerpersoons_wastafel=int(ruimte.get("meerpersoons_wastafel") or 0),
        douche=int(ruimte.get("douche") or 0),
        bad=int(ruimte.get("bad") or 0),
        baddouche=int(ruimte.get("baddouche") or 0),
    )


def maak_verkeersruimte(data: dict | None) -> VerkeersRuimte:
    ruimte = data or {}
    return VerkeersRuimte(
        naam=str(ruimte.get("naam") or RuimteNaam.VERKEERSRUIMTE),
        ruimte_m2=Decimal(str(ruimte.get("ruimte_m2") or 0)),
        verwarmd=bool(ruimte.get("verwarmd", False)),
        aantal_adressen_met_toegang_en_gebruiksrecht=int(
            ruimte.get("aantal_adressen_met_toegang_en_gebruiksrecht") or 1
        ),
    )


def maak_buitenruimte(data: dict | None) -> Buitenruimte:
    ruimte = data or {}
    naam = str(ruimte.get("naam") or "onbekende_buitenruimte")
    ruimte_m2 = Decimal(str(ruimte.get("ruimte_m2") or 0))
    if naam == RuimteNaam.GEMEENSCHAPPELIJKE_BUITENRUIMTE:
        return GemeenschappelijkeBuitenruimte(
            naam=naam,
            ruimte_m2=ruimte_m2,
            aantal_adressen_met_toegang_en_gebruiksrecht=int(
                ruimte.get("aantal_adressen_met_toegang_en_gebruiksrecht") or 1
            ),
        )
    return PriveBuitenruimte(
        naam=naam,
        ruimte_m2=ruimte_m2,
    )


def maak_parkeerruimte(data: dict | None) -> Parkeerruimte:
    ruimte = data or {}
    return Parkeerruimte(
        naam=str(ruimte.get("naam") or RuimteNaam.BUITENRUIMTE_PARKEERPLAATS),
        type=str(ruimte.get("type") or "onbekend"),
        aantal_adressen_met_toegang_en_gebruiksrecht=int(
            ruimte.get("aantal_adressen_met_toegang_en_gebruiksrecht") or 1
        ),
        laadpaal=bool(ruimte.get("laadpaal", False)),
    )


def _decimaal_of_none(waarde) -> Decimal | None:
    if waarde is None or waarde == "":
        return None
    return Decimal(str(waarde))
