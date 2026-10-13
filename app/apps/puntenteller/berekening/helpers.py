from decimal import ROUND_DOWN, ROUND_HALF_UP, Decimal
from typing import Iterable

from apps.puntenteller.resultaat import Regel


def waarde(getal: Decimal | int | None) -> Decimal:
    return Decimal(str(getal or 0))


def decimaal_of_none(getal: Decimal | int | str | None) -> Decimal | None:
    if getal is None:
        return None
    return Decimal(str(getal))


def som(waarden: Iterable[Decimal]) -> Decimal:
    return sum(waarden, Decimal("0"))


def als_tekst(veldnaam: str) -> str:
    return veldnaam.replace("_", " ").capitalize()


def nl(getal: Decimal | int) -> str:
    # Nederlandse notatie met maximaal 2 decimalen: 1234.5 -> "1.234,5".
    afgerond = Decimal(str(getal)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    tekst = f"{afgerond.normalize():,f}"
    return tekst.replace(",", "_").replace(".", ",").replace("_", ".")


def regel(
    omschrijving: str,
    aantal: Decimal | int,
    factor: Decimal,
    ruimte: str | None = None,
) -> Regel:
    return Regel(
        omschrijving=omschrijving,
        punten=waarde(aantal) * factor,
        ruimte=ruimte,
        aantal=aantal,
        factor=factor,
    )


def voorziening_regels(
    ruimte, velden: Iterable[str], kengetal, prefix: str
) -> list[Regel]:
    # Een regel per aanwezige voorziening, met kengetal <prefix>_<veld>_factor.
    return [
        regel(
            als_tekst(veld),
            getattr(ruimte, veld),
            getattr(kengetal, f"{prefix}_{veld}_factor"),
            ruimte.naam,
        )
        for veld in velden
        if getattr(ruimte, veld)
    ]


def eigen_ruimte(ruimte) -> bool:
    # Een ruimte waar alleen dit adres toegang en gebruiksrecht toe heeft.
    return ruimte.aantal_adressen_met_toegang_en_gebruiksrecht <= 1


def gedeeld_door_adressen(regels: list[Regel], ruimte) -> list[Regel]:
    # Gedeelde ruimten worden gedeeld door het aantal adressen met toegang en
    # gebruiksrecht. Het verschil wordt een aparte regel.
    aantal_adressen = max(ruimte.aantal_adressen_met_toegang_en_gebruiksrecht or 0, 1)
    punten = som(r.punten for r in regels)
    if aantal_adressen == 1 or not punten:
        return regels
    return [
        *regels,
        Regel(
            omschrijving=f"Gedeeld door {aantal_adressen} adressen",
            punten=punten / Decimal(aantal_adressen) - punten,
            ruimte=ruimte.naam,
        ),
    ]


def begrensd(
    regels: list[Regel], maximum: Decimal, omschrijving: str, ruimte: str | None = None
) -> list[Regel]:
    # Voegt een regel toe die het totaal van de regels terugbrengt tot het maximum.
    punten = som(r.punten for r in regels)
    if punten <= maximum:
        return regels
    return [
        *regels,
        Regel(omschrijving=omschrijving, punten=maximum - punten, ruimte=ruimte),
    ]


def afgerond_op_kwart_punt(regels: list[Regel]) -> list[Regel]:
    # Beleidsboek 2.1.4: het totaal van een rubriek wordt afgerond op 0,25 punt.
    # Het verschil wordt een afrondingsregel.
    punten = som(r.punten for r in regels)
    afgerond = afronden_op_kwart_punt(punten)
    # Ook zonder verschil is een afrondingsregel nodig als regels meer dan
    # 2 decimalen hebben: die vangt dan de weergave-afronding op.
    if afgerond == punten and all(op_twee_decimalen(r.punten) for r in regels):
        return regels
    return [
        *regels,
        Regel("Afronding op kwartpunt", afgerond - punten, afronding=True),
    ]


def op_twee_decimalen(getal: Decimal) -> bool:
    return getal == getal.quantize(Decimal("0.01"))


def afronden_op_kwart_punt(getal: Decimal) -> Decimal:
    # Beleidsboek 2.1.4: afronden op 0,25 punt, vanaf 1/8 punt naar boven.
    return (getal * Decimal("4")).quantize(
        Decimal("1"), rounding=ROUND_HALF_UP
    ) / Decimal("4")


def afronden_op_hele_m2(getal: Decimal) -> int:
    # Beleidsboek 2.11.2: bij 0,5 m2 of meer wordt naar boven afgerond, anders naar beneden.
    return int(getal.quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def afronden_op_hele_punten(getal: Decimal) -> Decimal:
    # Beleidsboek 2.1.5: het eindsaldo van de woonruimte wordt op hele punten afgerond.
    return getal.quantize(Decimal("1"), rounding=ROUND_HALF_UP)


def afronden_naar_beneden_op_hele_punten(getal: Decimal) -> Decimal:
    # Beleidsboek 2.11.2 en 2.11.7: naar beneden afronden op hele punten.
    return getal.quantize(Decimal("1"), rounding=ROUND_DOWN)
