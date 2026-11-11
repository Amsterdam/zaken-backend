from dataclasses import replace
from decimal import Decimal

from apps.puntenteller.berekening.helpers import (
    begrensd,
    eigen_ruimte,
    nl,
    voorziening_regels,
    zonder_ruimte,
)
from apps.puntenteller.models import Kengetal
from apps.puntenteller.resultaat import Regel, Rubriek
from apps.puntenteller.ruimte_types import KeukenRuimte, Ruimten

# Extra keukenvoorzieningen met een vaste factor per stuk (kengetal keuken_<veld>_factor).
KEUKEN_EXTRA_VOORZIENINGEN = (
    "inbouw_afzuiginstallatie",
    "inbouw_kookplaat_inductie",
    "inbouw_kookplaat_keramisch",
    "inbouw_kookplaat_gas",
    "inbouw_koelkast",
    "inbouw_vrieskast",
    "inbouw_oven_elektrisch",
    "inbouw_oven_gas",
    "inbouw_magnetron",
    "inbouw_vaatwasmachine",
    "extra_kastruimte",
    "eenhandsmengkraan",
    "thermostatische_mengkraan",
    "kokendwaterfunctie",
)


def keuken_rubriek(ruimten: Ruimten, kengetal: Kengetal) -> Rubriek:
    # Gedeelde keukens vallen onder rubriek 9.
    return Rubriek(
        "Keuken",
        zonder_ruimte(
            [
                r
                for keuken in ruimten.keukens
                if eigen_ruimte(keuken)
                for r in keuken_regels(keuken, kengetal)
            ]
        ),
    )


def keuken_regels(keuken: KeukenRuimte, kengetal: Kengetal) -> list[Regel]:
    keuken = _met_kookfunctie_kranen_uitgesplitst(keuken)
    aanrecht = _aanrecht_regel(keuken, kengetal)
    # Beleidsboek 2.5.3: de extra keukenvoorzieningen per keuken worden
    # afgetopt op de punten voor de basisvoorzieningen van het aanrecht.
    extra = begrensd(
        voorziening_regels(keuken, KEUKEN_EXTRA_VOORZIENINGEN, kengetal, "keuken"),
        aanrecht.punten,
        "Extra voorzieningen afgetopt op de punten voor het aanrecht",
        keuken.naam,
    )
    return [aanrecht, *extra]


def _aanrecht_regel(keuken: KeukenRuimte, kengetal: Kengetal) -> Regel:
    # Beleidsboek 2.5.2: minder dan 1 meter = 0, tot en met 2 meter = 4,
    # en alleen langer dan 2 meter = 7 punten.
    meters = keuken.aanrechtlengte_meters or Decimal("0")
    grens_1 = kengetal.keuken_aanrecht_grens_1
    grens_2 = kengetal.keuken_aanrecht_grens_2
    if meters < grens_1:
        omschrijving = f"Aanrecht korter dan {nl(grens_1)} m"
        punten = kengetal.keuken_aanrecht_punten_1
    elif meters <= grens_2:
        omschrijving = f"Aanrecht tot en met {nl(grens_2)} m"
        punten = kengetal.keuken_aanrecht_punten_2
    else:
        omschrijving = f"Aanrecht langer dan {nl(grens_2)} m"
        punten = kengetal.keuken_aanrecht_punten_3
    return Regel(omschrijving, punten, ruimte=keuken.naam, aantal=meters)


def _met_kookfunctie_kranen_uitgesplitst(keuken: KeukenRuimte) -> KeukenRuimte:
    # Beleidsboek 2.5.3 kent de mengkraan en de kokendwaterfunctie als aparte
    # voorzieningen; een mengkraan met kookfunctie is ze allebei. Zo blijven de
    # regels in het resultaat die van het beleidsboek.
    eenhands = keuken.eenhandsmengkraan_kookfunctie
    thermostatisch = keuken.thermostatische_mengkraan_kookfunctie
    return replace(
        keuken,
        eenhandsmengkraan=keuken.eenhandsmengkraan + eenhands,
        thermostatische_mengkraan=keuken.thermostatische_mengkraan + thermostatisch,
        kokendwaterfunctie=keuken.kokendwaterfunctie + eenhands + thermostatisch,
        eenhandsmengkraan_kookfunctie=0,
        thermostatische_mengkraan_kookfunctie=0,
    )
