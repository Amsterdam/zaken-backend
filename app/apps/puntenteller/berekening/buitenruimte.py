from decimal import Decimal

from apps.puntenteller.berekening.helpers import (
    als_tekst,
    begrensd,
    gedeeld_door_adressen,
    nl,
    regel,
)
from apps.puntenteller.models import Kengetal
from apps.puntenteller.resultaat import Regel, Rubriek
from apps.puntenteller.ruimte_types import (
    PARKEERRUIMTE_TYPES,
    GemeenschappelijkeBuitenruimte,
    Parkeerruimte,
    PriveBuitenruimte,
    Ruimten,
)


def buitenruimte_rubriek(ruimten: Ruimten, kengetal: Kengetal) -> Rubriek:
    # Beleidsboek 2.8.1, 2.8.2 en 2.8.4: prive- en gemeenschappelijke
    # buitenruimten worden met aparte m2-systematiek gewaardeerd.
    if not ruimten.buitenruimten:
        return Rubriek(
            "Buitenruimten",
            [
                Regel(
                    "Geen buitenruimte",
                    -kengetal.buitenruimte_geen_buitenruimte_aftrek,
                )
            ],
        )

    regels = []
    if any(isinstance(r, PriveBuitenruimte) for r in ruimten.buitenruimten):
        regels.append(
            Regel(
                "Basispunten privé buitenruimte",
                kengetal.buitenruimte_prive_basispunten,
            )
        )
    for ruimte in ruimten.buitenruimten:
        if isinstance(ruimte, PriveBuitenruimte):
            regels.append(
                regel(
                    "Oppervlakte in m²",
                    ruimte.ruimte_m2,
                    kengetal.buitenruimte_prive_punten_per_m2,
                    ruimte.naam,
                )
            )
        elif isinstance(ruimte, GemeenschappelijkeBuitenruimte):
            regels += gedeeld_door_adressen(
                [
                    regel(
                        "Oppervlakte in m²",
                        ruimte.ruimte_m2,
                        kengetal.buitenruimte_gemeenschappelijke_punten_per_m2,
                        ruimte.naam,
                    )
                ],
                ruimte,
            )
    maximum = kengetal.buitenruimte_max_punten
    return Rubriek(
        "Buitenruimten",
        begrensd(regels, maximum, f"Maximaal {nl(maximum)} punten"),
    )


def parkeren_rubriek(ruimten: Ruimten, kengetal: Kengetal) -> Rubriek:
    # Beleidsboek 2.10.3: parkeerplaatsen worden per object gewaardeerd op type,
    # met deling door het aantal adressen met exclusieve toegang en gebruiksrecht.
    # Plekken met hetzelfde aantal adressen staan samen in één regel per type.
    groepen: dict[tuple[str, int], list[Parkeerruimte]] = {}
    for parkeerruimte in ruimten.parkeerruimten:
        sleutel = (
            parkeerruimte.naam,
            parkeerruimte.aantal_adressen_met_toegang_en_gebruiksrecht,
        )
        groepen.setdefault(sleutel, []).append(parkeerruimte)

    regels = []
    for parkeerruimten in groepen.values():
        regels += gedeeld_door_adressen(
            _parkeerruimte_regels(parkeerruimten, kengetal), parkeerruimten[0]
        )
    return Rubriek("Parkeren", regels)


def _parkeerruimte_regels(
    parkeerruimten: list[Parkeerruimte], kengetal: Kengetal
) -> list[Regel]:
    naam = parkeerruimten[0].naam
    regels = []
    for type_naam in PARKEERRUIMTE_TYPES:
        aantal = sum(1 for p in parkeerruimten if p.type == type_naam)
        if aantal:
            factor = Decimal(
                str(getattr(kengetal, f"parkeerruimte_{type_naam}_factor"))
            )
            regels.append(regel(als_tekst(type_naam), aantal, factor, naam))
    laadpalen = sum(1 for p in parkeerruimten if p.laadpaal)
    if laadpalen:
        regels.append(
            regel(
                "Laadpaal",
                laadpalen,
                kengetal.bijzondere_voorziening_laadpaal_factor,
                naam,
            )
        )
    return regels
