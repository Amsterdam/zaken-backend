from datetime import date
from decimal import Decimal

from apps.puntenteller.berekening.helpers import (
    afronden_op_hele_punten,
    nl,
    op_twee_decimalen,
)
from apps.puntenteller.models import Gebruikersinvoer, Kengetal
from apps.puntenteller.resultaat import Huurprijsopslag, Regel, Rubriek

WET_BETAALBARE_HUUR_INGANGSDATUM = date(2024, 7, 1)
MONUMENT_NAMEN = {
    "rijksmonument": "Rijksmonument",
    "gemeentelijk_monument": "Gemeentelijk monument",
    "provinciaal_monument": "Provinciaal monument",
    "beschermd_stads_of_dorpsgezicht": "Beschermd stads- of dorpsgezicht",
}
# Beleidsboek 2.4.6.1: rijks-, provinciale en gemeentelijke monumenten. Een
# beschermd stads- of dorpsgezicht valt hier niet onder.
MONUMENTEN = {"rijksmonument", "gemeentelijk_monument", "provinciaal_monument"}
BESCHERMD_GEZICHT_BOUWJAAR_VOOR = 1965
# Beleidsboek 1.3.1: de middensector loopt van 144 t/m 186 punten.
MIDDENSECTOR_MINIMUM_PUNTEN = Decimal("144")
MIDDENSECTOR_MAXIMUM_PUNTEN = Decimal("186")


def monument_soort(invoer: Gebruikersinvoer) -> str:
    if not invoer.monument:
        return ""
    return (invoer.monument_soort or "").strip().lower()


def zorgwoning_opslag(
    basis: Decimal, invoer: Gebruikersinvoer, kengetal: Kengetal
) -> Rubriek | None:
    if not invoer.zorgwoning:
        return None
    # Beleidsboek 2.1.5 en 2.12: de 35%-toeslag voor zorgwoningen gaat over de
    # rubrieken 1 t/m 11.1. Niet afronden op kwartpunten: pas het eindtotaal
    # wordt afgerond, net als bij de Huurcommissie.
    factor = Decimal(str(kengetal.zorgwoning_opslag_factor))
    return Rubriek(
        "Zorgwoning",
        [
            Regel(
                f"Toeslag {_procent(factor)} over {nl(basis)} punten "
                "(rubriek 1 t/m 11.1)",
                basis * (factor - 1),
            )
        ],
    )


def rijksmonument_extra_punten(
    invoer: Gebruikersinvoer, kengetal: Kengetal
) -> Rubriek | None:
    # Beleidsboek 2.13.3: bij een huurovereenkomst van voor de Wet betaalbare
    # huur krijgt een rijksmonument extra punten in plaats van een huurprijsopslag.
    if monument_soort(invoer) != "rijksmonument" or not _contract_voor_wbh(invoer):
        return None
    return Rubriek(
        "Rijksmonument",
        [
            Regel(
                "Extra punten (huurovereenkomst voor 1 juli 2024)",
                Decimal(str(kengetal.monument_rijksmonument_extra_punten)),
            )
        ],
    )


def huurprijsopslagen(
    invoer: Gebruikersinvoer, kengetal: Kengetal, totaal_punten: Decimal
) -> list[Huurprijsopslag]:
    # Beleidsboek 2.13: deze opslagen verhogen de maximale huurprijs, niet het
    # puntenaantal. Bij samenloop worden de percentages opgeteld (2.13.1).
    opslagen = []
    soort = monument_soort(invoer)
    factor = None
    if soort == "rijksmonument" and not _contract_voor_wbh(invoer):
        factor = kengetal.monument_rijksmonument_huurprijsopslag_factor
    elif soort in {"gemeentelijk_monument", "provinciaal_monument"}:
        factor = kengetal.monument_gemeentelijk_of_provinciaal_huurprijsopslag_factor
    elif soort == "beschermd_stads_of_dorpsgezicht" and _gebouwd_voor_1965(invoer):
        factor = (
            kengetal.monument_beschermd_stads_of_dorpsgezicht_huurprijsopslag_factor
        )
    if factor is not None:
        opslagen.append(Huurprijsopslag(MONUMENT_NAMEN[soort], _procentpunten(factor)))
    # Beleidsboek 2.13.6.1: nieuwbouwopslag alleen in de middensector.
    if invoer.nieuwbouw and (
        MIDDENSECTOR_MINIMUM_PUNTEN <= totaal_punten <= MIDDENSECTOR_MAXIMUM_PUNTEN
    ):
        opslagen.append(
            Huurprijsopslag(
                "Nieuwbouw", _procentpunten(kengetal.nieuwbouw_huurprijsopslag_factor)
            )
        )
    return opslagen


def afronding_opslag(totaal: Decimal, opslagen: list[Rubriek]) -> Rubriek | None:
    # Beleidsboek 2.1.5: het eindsaldo van de woonruimte wordt op hele punten afgerond.
    afgerond = afronden_op_hele_punten(totaal)
    if afgerond == totaal and all(op_twee_decimalen(o.punten) for o in opslagen):
        return None
    return Rubriek(
        "Afronding",
        [Regel("Afronding op hele punten", afgerond - totaal, afronding=True)],
    )


def _gebouwd_voor_1965(invoer: Gebruikersinvoer) -> bool:
    # Beleidsboek 2.13.5: de opslag voor beschermd stads- of dorpsgezicht geldt
    # alleen voor woningen gebouwd vóór 1965. Zonder bouwjaar geen opslag.
    return bool(invoer.bouwjaar) and invoer.bouwjaar < BESCHERMD_GEZICHT_BOUWJAAR_VOOR


def _contract_voor_wbh(invoer: Gebruikersinvoer) -> bool:
    afgesloten_op = invoer.huurovereenkomst_afgesloten_op
    return (
        afgesloten_op is not None and afgesloten_op < WET_BETAALBARE_HUUR_INGANGSDATUM
    )


def _procentpunten(factor) -> Decimal:
    return (Decimal(str(factor)) - 1) * 100


def _procent(factor: Decimal) -> str:
    return f"{nl(_procentpunten(factor))}%"
