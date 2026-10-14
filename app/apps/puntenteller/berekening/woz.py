from datetime import date
from decimal import Decimal

from apps.puntenteller.berekening.helpers import (
    afgerond_op_kwart_punt,
    afronden_naar_beneden_op_hele_punten,
    afronden_op_hele_m2,
    decimaal_of_none,
    geldend_op,
    nl,
    waarde,
)
from apps.puntenteller.berekening.oppervlakte import (
    overige_ruimten_oppervlakte,
    vertrekken_oppervlakte,
)
from apps.puntenteller.models import Gebruikersinvoer, Kengetal
from apps.puntenteller.resultaat import Regel, Rubriek
from apps.puntenteller.ruimte_types import Ruimten

WOZ_CAP_PERCENTAGE = Decimal("0.33")
WOZ_GRENS = Decimal("187")
WOZ_MINIMALE_WAARDERING = Decimal("186")
WOZ_MINIMUM_NIEUWBOUW_2015_2019 = Decimal("40")
NIEUWBOUW_2015_2019_MINIMUM_OVERIGE_PUNTEN = Decimal("110")


def woz_rubriek(
    invoer: Gebruikersinvoer, ruimten: Ruimten, kengetal: Kengetal
) -> Rubriek:
    return Rubriek("WOZ-waarde", _woz_regels(invoer, ruimten, kengetal))


def nieuwbouw_2015_2019_uitzondering(
    invoer: Gebruikersinvoer, overige_punten: Decimal
) -> bool:
    # Beleidsboek 2.11.5: alleen als rubriek 1 t/m 10 en 12 samen minimaal
    # 110 punten halen.
    return bool(invoer.woz_nieuwbouw_2015_2019) and (
        overige_punten >= NIEUWBOUW_2015_2019_MINIMUM_OVERIGE_PUNTEN
    )


def nieuwbouw_2015_2019_regels(
    invoer: Gebruikersinvoer, overige_punten: Decimal
) -> list[Regel]:
    # Toelichting als nieuwbouw 2015-2019 is opgegeven, maar niet van toepassing is.
    if not invoer.woz_nieuwbouw_2015_2019 or nieuwbouw_2015_2019_uitzondering(
        invoer, overige_punten
    ):
        return []
    return [
        Regel(
            "Geen minimum voor nieuwbouw 2015-2019: minder dan "
            f"{nl(NIEUWBOUW_2015_2019_MINIMUM_OVERIGE_PUNTEN)} punten in de "
            "overige rubrieken",
            Decimal("0"),
        )
    ]


def woz_minimum_nieuwbouw_rubriek(
    woz_punten: Decimal, uitzondering: bool
) -> Rubriek | None:
    # Beleidsboek 2.11.5 (rubriek 11.2 van het Bhw): voor nieuwbouw uit
    # 2015-2019 geldt minimaal 40 WOZ-punten. Deze punten tellen niet mee voor de
    # zorgwoningtoeslag.
    if not uitzondering or woz_punten >= WOZ_MINIMUM_NIEUWBOUW_2015_2019:
        return None
    return Rubriek(
        "WOZ-waarde nieuwbouw 2015-2019",
        [
            Regel(
                f"Aanvulling tot minimaal {nl(WOZ_MINIMUM_NIEUWBOUW_2015_2019)} "
                "WOZ-punten",
                WOZ_MINIMUM_NIEUWBOUW_2015_2019 - woz_punten,
            )
        ],
    )


def woz_cap_regels(
    woz_punten: Decimal,
    overige_punten: Decimal,
    invoer: Gebruikersinvoer,
    nieuwbouw_uitzondering: bool,
) -> list[Regel]:
    # Beleidsboek 2.11.2 en 2.11.7: WOZ mag maximaal 33% van het totale
    # puntenaantal vormen. Niet onder 187 punten, niet bij nieuwbouw 2015-2019
    # (2.11.5) en niet bij de minimum WOZ-waarde.
    if woz_punten <= 0 or overige_punten <= 0:
        return []
    if overige_punten + woz_punten < WOZ_GRENS or nieuwbouw_uitzondering:
        return []
    if gebruikt_minimum_woz_waarde(invoer):
        return []

    # Omgerekend naar de overige punten: max_woz = (33% / 67%) * overige_punten.
    maximum = (
        WOZ_CAP_PERCENTAGE / (Decimal("1") - WOZ_CAP_PERCENTAGE)
    ) * overige_punten
    if woz_punten <= maximum:
        return []

    # Beleidsboek 2.11.7: bij toepassing van de cap naar beneden afronden op hele punten.
    woz_na_cap = afronden_naar_beneden_op_hele_punten(maximum)
    regels = [
        Regel(
            f"Afgetopt op {nl(WOZ_CAP_PERCENTAGE * 100)}% van het totaal",
            woz_na_cap - woz_punten,
        )
    ]
    # Beleidsboek 2.11.7: door de cap zakt de woning niet onder 186 punten,
    # behalve bij kleine nieuwbouwwoningen.
    totaal_na_cap = overige_punten + woz_na_cap
    if totaal_na_cap < WOZ_GRENS and not invoer.woz_kleine_nieuwbouwwoning:
        regels.append(
            Regel(
                f"Minimale waardering {nl(WOZ_MINIMALE_WAARDERING)} punten",
                WOZ_MINIMALE_WAARDERING - totaal_na_cap,
            )
        )
    return regels


def gebruikt_minimum_woz_waarde(invoer: Gebruikersinvoer) -> bool:
    # Beleidsboek 2.11.1: zonder WOZ-waarde geldt de minimum WOZ-waarde.
    return not invoer.woz_waarde


def _woz_regels(
    invoer: Gebruikersinvoer, ruimten: Ruimten, kengetal: Kengetal
) -> list[Regel]:
    if gebruikt_minimum_woz_waarde(invoer):
        # Beleidsboek 2.11.1 en 2.11.2: de minimum WOZ-waarde die nu geldt, met
        # de kengetallen die nu gelden.
        vandaag = date.today()
        woz_waarde = _minimum_woz_waarde(kengetal, vandaag)
        peiljaar = _peiljaar_op(kengetal, vandaag)
        if woz_waarde is None or peiljaar is None:
            return [Regel("Geen WOZ-waarde en geen minimum WOZ-waarde", Decimal("0"))]
        woz_tekst = f"minimum WOZ-waarde € {nl(woz_waarde)}"
    else:
        peiljaar = invoer.woz_peildatum_jaar or 0
        if not peiljaar:
            return [Regel("Geen WOZ-peiljaar opgegeven", Decimal("0"))]
        woz_waarde = _woz_waarde_na_bouwcorrectie(invoer)
        woz_tekst = f"€ {nl(woz_waarde.quantize(Decimal('1')))}"
    kengetallen = _woz_kengetallen_per_peiljaar(kengetal).get(peiljaar)
    if kengetallen is None:
        return [Regel(f"Geen WOZ-kengetallen voor peiljaar {peiljaar}", Decimal("0"))]

    # Beleidsboek 2.11.2 en 2.11.4: onderdeel II rekent met m2 van vertrekken,
    # overige ruimten en type I parkeren, afgerond op hele m2. Een gedeelde
    # parkeerplek telt mee naar het aandeel per adres, net als bij de Huurcommissie.
    parkeer_oppervlakte = sum(
        (
            Decimal(str(kengetal.woz_oppervlakte_parkeer_type_1))
            / max(parkeerruimte.aantal_adressen_met_toegang_en_gebruiksrecht, 1)
            for parkeerruimte in ruimten.parkeerruimten
            if parkeerruimte.type == "gesloten_garage_bij_complex"
        ),
        Decimal("0"),
    )
    oppervlakte = afronden_op_hele_m2(
        vertrekken_oppervlakte(ruimten)
        + overige_ruimten_oppervlakte(ruimten)
        + parkeer_oppervlakte
    )
    if woz_waarde <= 0 or oppervlakte <= 0:
        return [Regel("Geen WOZ-waarde of oppervlakte", Decimal("0"))]

    # Beleidsboek 2.11.6: kleine nieuwbouwwoningen in COROP Amsterdam/Utrecht
    # gebruiken een afwijkend onderdeel-II-kengetal.
    if invoer.woz_kleine_nieuwbouwwoning:
        kengetal_2 = kengetallen["onderdeel_2_kleine_nieuwbouwwoning"]
        toelichting_2 = ", kleine nieuwbouwwoning"
    else:
        kengetal_2 = kengetallen["onderdeel_2"]
        toelichting_2 = ""

    regels = [
        # Beleidsboek 2.11.2: onderdeel I is 1 punt per bedrag aan WOZ-waarde.
        Regel(
            f"Onderdeel I: {woz_tekst} / {nl(kengetallen['onderdeel_1'])}",
            woz_waarde / kengetallen["onderdeel_1"],
        ),
        # Beleidsboek 2.11.2: onderdeel II is WOZ gedeeld door relevante m2 en
        # daarna door het tweede kengetal.
        Regel(
            f"Onderdeel II: {woz_tekst} / ({oppervlakte} m² × {nl(kengetal_2)}"
            f"{toelichting_2})",
            woz_waarde / (Decimal(oppervlakte) * kengetal_2),
        ),
    ]

    # Beleidsboek 2.11.2 in samenhang met de afrondingsinstructie: totaal wordt
    # afgerond op een kwart punt.
    return afgerond_op_kwart_punt(regels)


def _woz_waarde_na_bouwcorrectie(invoer: Gebruikersinvoer) -> Decimal:
    # Beleidsboek 2.11.4: bij gebouwd eigendom in aanbouw wordt gerekend met de
    # waarde alsof de bouw 100% is voltooid.
    woz_waarde = waarde(invoer.woz_waarde)
    percentage = decimaal_of_none(invoer.woz_bouwvoltooiingspercentage)
    if percentage is None or not 0 < percentage < 100:
        return woz_waarde
    return woz_waarde / (percentage / Decimal("100"))


def _minimum_woz_waarde(kengetal: Kengetal, peildatum: date) -> Decimal | None:
    geldig = geldend_op(kengetal.woz_minimum_waarde_per_ingangsdatum, peildatum)
    return Decimal(str(geldig[1])) if geldig else None


def _peiljaar_op(kengetal: Kengetal, peildatum: date) -> int | None:
    # Beleidsboek 2.11.2: de kengetallen per 1 januari horen bij de
    # waardepeildatum van het jaar ervoor.
    peiljaren = [
        jaar
        for jaar in _woz_kengetallen_per_peiljaar(kengetal)
        if jaar <= peildatum.year - 1
    ]
    return max(peiljaren) if peiljaren else None


def _woz_kengetallen_per_peiljaar(kengetal: Kengetal) -> dict[int, dict[str, Decimal]]:
    # Beleidsboek 2.11.2: de bedragen voor onderdeel I en II verschillen per waardepeildatum.
    return {
        int(peiljaar): {
            sleutel: Decimal(str(bedrag)) for sleutel, bedrag in kengetallen.items()
        }
        for peiljaar, kengetallen in kengetal.woz_kengetallen_per_peiljaar.items()
    }
