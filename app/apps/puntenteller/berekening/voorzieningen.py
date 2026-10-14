from decimal import Decimal

from apps.puntenteller.berekening.helpers import (
    afronden_naar_beneden_op_hele_punten,
    nl,
    regel,
    waarde,
)
from apps.puntenteller.models import Gebruikersinvoer, Kengetal
from apps.puntenteller.resultaat import Regel, Rubriek


def woonvoorzieningen_handicap_rubriek(
    invoer: Gebruikersinvoer, kengetal: Kengetal
) -> Rubriek:
    regels = []
    bedrag_per_punt = Decimal(str(kengetal.woonvoorziening_handicap_bedrag_per_punt))
    investering = waarde(invoer.woonvoorziening_handicap_netto_investering)
    if invoer.woonvoorziening_handicap and investering and bedrag_per_punt > 0:
        # Beleidsboek 2.7: 1 punt per 332 euro netto-investering. Net als de
        # Huurcommissie alleen hele punten per volle 332 euro.
        punten = investering / bedrag_per_punt
        regels.append(
            Regel(
                f"Netto-investering € {nl(investering)} / € {nl(bedrag_per_punt)} "
                "per punt",
                punten,
            )
        )
        afgerond = afronden_naar_beneden_op_hele_punten(punten)
        if afgerond != punten:
            regels.append(
                Regel(
                    f"Alleen hele punten per volle € {nl(bedrag_per_punt)}",
                    afgerond - punten,
                    afronding=True,
                )
            )
    return Rubriek(
        "Woonvoorzieningen voor personen met een handicap",
        regels,
    )


def bijzondere_voorzieningen_rubriek(
    invoer: Gebruikersinvoer, kengetal: Kengetal
) -> Rubriek:
    # Beleidsboek 2.12.2 en 2.12.3: aanbelfunctie en losse laadpalen tellen
    # als bijzondere voorzieningen in deze rubriek.
    regels = []
    if invoer.bijzondere_voorziening_intercom_met_beeld:
        regels.append(
            Regel(
                "Intercom met beeld",
                kengetal.bijzondere_voorziening_intercom_met_beeld_factor,
            )
        )
    if invoer.bijzondere_voorziening_laadpalen:
        regels.append(
            regel(
                "Laadpalen",
                invoer.bijzondere_voorziening_laadpalen,
                kengetal.bijzondere_voorziening_laadpaal_factor,
            )
        )
    return Rubriek("Bijzondere voorzieningen", regels)
