from decimal import Decimal

from apps.puntenteller.berekening.helpers import eigen_ruimte, gedeeld_door_adressen
from apps.puntenteller.berekening.keuken import keuken_regels
from apps.puntenteller.berekening.oppervlakte import oppervlakte_regels
from apps.puntenteller.berekening.sanitair import sanitair_regels
from apps.puntenteller.berekening.verwarming import verwarming_regels_per_ruimte
from apps.puntenteller.models import Gebruikersinvoer, Kengetal
from apps.puntenteller.resultaat import Regel, Rubriek
from apps.puntenteller.ruimte_types import KeukenRuimte, Ruimten, VerkeersRuimte

ZORGWONING_GEMEENSCHAPPELIJKE_RUIMTEN_PUNTEN = Decimal("3")


def gemeenschappelijke_ruimten_rubriek(
    invoer: Gebruikersinvoer, ruimten: Ruimten, kengetal: Kengetal
) -> Rubriek:
    naam = "Gemeenschappelijke ruimten"
    gedeelde_ruimten = [
        ruimte
        for ruimte in [
            *ruimten.vertrekken,
            *ruimten.overige_ruimten,
            *ruimten.verkeersruimten,
        ]
        if not eigen_ruimte(ruimte)
    ]
    if invoer.zorgwoning and gedeelde_ruimten:
        # Beleidsboek 2.9.4: bij een zorgwoning worden de gemeenschappelijke
        # ruimten niet gemeten, maar met vaste punten per woning gewaardeerd.
        # Zonder gedeelde ruimten geen punten, net als bij de Huurcommissie.
        return Rubriek(
            naam,
            [
                Regel(
                    "Vaste waardering bij een zorgwoning",
                    ZORGWONING_GEMEENSCHAPPELIJKE_RUIMTEN_PUNTEN,
                )
            ],
        )

    # Beleidsboek 2.9.7: per gedeelde ruimte de punten voor oppervlakte,
    # verwarming, keuken en sanitair optellen en delen door het aantal adressen.
    regels = []
    for ruimte in gedeelde_ruimten:
        ruimte_regels = verwarming_regels_per_ruimte(ruimte, kengetal)
        if not isinstance(ruimte, VerkeersRuimte):
            ruimte_regels = [
                *oppervlakte_regels(ruimte, kengetal),
                *ruimte_regels,
                *sanitair_regels(ruimte, kengetal),
            ]
        if isinstance(ruimte, KeukenRuimte):
            ruimte_regels += keuken_regels(ruimte, kengetal)
        regels += gedeeld_door_adressen(ruimte_regels, ruimte)
    return Rubriek(naam, regels)
