from decimal import Decimal

from apps.puntenteller.berekening.helpers import (
    afronden_op_hele_m2,
    eigen_ruimte,
    nl,
    regel,
    som,
)
from apps.puntenteller.models import Kengetal
from apps.puntenteller.resultaat import Regel, Rubriek
from apps.puntenteller.ruimte_types import (
    MINIMALE_OPPERVLAKTE_VERTREK,
    OverigeRuimte,
    Ruimten,
    VertrekRuimte,
    ZolderRuimte,
)

MINIMALE_OPPERVLAKTE_OVERIGE_RUIMTE = Decimal("2.00")
AFTREK_ZOLDER_ZONDER_VASTE_TRAP = Decimal("5")


def vertrekken_oppervlakte(ruimten: Ruimten) -> Decimal:
    return som(ruimte.ruimte_m2 for ruimte in ruimten.vertrekken)


def vertrekken_rubriek(ruimten: Ruimten, kengetal: Kengetal) -> Rubriek:
    # Beleidsboek hoofdstuk 2, rubriek 1 en paragraaf 2.2: vertrekken tellen mee
    # tegen 1 punt per m2. Gedeelde vertrekken vallen onder rubriek 9.
    eigen = [r for r in ruimten.vertrekken if eigen_ruimte(r)]
    regels = [r for ruimte in eigen for r in oppervlakte_regels(ruimte, kengetal)]
    regels += _afronding_op_hele_m2(
        [r.ruimte_m2 for r in eigen], kengetal.vertrekken_factor
    )
    for ruimte in ruimten.te_kleine_vertrekken:
        regels.append(
            Regel(
                f"Kleiner dan {nl(MINIMALE_OPPERVLAKTE_VERTREK)} m², gewaardeerd als "
                "overige ruimte",
                Decimal("0"),
                ruimte=ruimte.naam,
                aantal=ruimte.ruimte_m2,
            )
        )
    return Rubriek("Oppervlakte vertrekken", regels)


def overige_ruimten_oppervlakte(ruimten: Ruimten) -> Decimal:
    return som(_effectieve_oppervlakte(ruimte) for ruimte in ruimten.overige_ruimten)


def overige_ruimten_rubriek(ruimten: Ruimten, kengetal: Kengetal) -> Rubriek:
    # Beleidsboek hoofdstuk 2, rubriek 2 en paragraaf 2.2: overige ruimten tellen
    # mee tegen 0,75 punt per m2. Gedeelde overige ruimten vallen onder rubriek 9.
    eigen = [r for r in ruimten.overige_ruimten if eigen_ruimte(r)]
    regels = [r for ruimte in eigen for r in oppervlakte_regels(ruimte, kengetal)]
    regels += _afronding_op_hele_m2(
        [_effectieve_oppervlakte(r) for r in eigen], kengetal.overige_ruimte_factor
    )
    return Rubriek("Oppervlakte overige ruimten", regels)


def oppervlakte_regels(
    ruimte: VertrekRuimte | OverigeRuimte, kengetal: Kengetal
) -> list[Regel]:
    if not ruimte.ruimte_m2:
        return []
    if isinstance(ruimte, OverigeRuimte):
        return _overige_ruimte_regels(ruimte, kengetal)
    return [
        regel(
            "Oppervlakte in m²",
            ruimte.ruimte_m2,
            kengetal.vertrekken_factor,
            ruimte.naam,
        )
    ]


def _afronding_op_hele_m2(oppervlakten: list[Decimal], factor: Decimal) -> list[Regel]:
    # Beleidsboek 2.2.1.1 en 2.2.2.1: de m² van de ruimten samen worden
    # afgerond op hele m², vanaf 0,50 m² naar boven.
    totaal = som(oppervlakten)
    afgerond = afronden_op_hele_m2(totaal)
    if afgerond == totaal:
        return []
    return [
        regel(
            f"Afronding op hele m² ({nl(totaal)} m² wordt {afgerond} m²)",
            afgerond - totaal,
            factor,
        )
    ]


def _effectieve_oppervlakte(ruimte: OverigeRuimte) -> Decimal:
    oppervlakte = ruimte.ruimte_m2 - _loopruimte(ruimte)
    if oppervlakte < MINIMALE_OPPERVLAKTE_OVERIGE_RUIMTE:
        # Beleidsboek 2.2.2.2 lid 2 en 2.2.2.4: overige ruimten kleiner dan 2 m2
        # tellen niet mee.
        return Decimal("0")
    return oppervlakte


def _loopruimte(ruimte: OverigeRuimte) -> Decimal:
    # Loopruimte naar een andere ruimte via de zolder telt niet mee.
    if isinstance(ruimte, ZolderRuimte) and ruimte.aftrek_loopruimte_m2 is not None:
        return min(ruimte.aftrek_loopruimte_m2, ruimte.ruimte_m2)
    return Decimal("0")


def _overige_ruimte_regels(ruimte: OverigeRuimte, kengetal: Kengetal) -> list[Regel]:
    oppervlakte = _effectieve_oppervlakte(ruimte)
    if not oppervlakte:
        return [
            Regel(
                f"Kleiner dan {nl(MINIMALE_OPPERVLAKTE_OVERIGE_RUIMTE)} m², telt niet mee",
                Decimal("0"),
                ruimte=ruimte.naam,
                aantal=ruimte.ruimte_m2 - _loopruimte(ruimte),
            )
        ]

    omschrijving = "Oppervlakte in m²"
    if _loopruimte(ruimte):
        omschrijving += f" (na aftrek {nl(_loopruimte(ruimte))} m² loopruimte)"
    regels = [
        regel(omschrijving, oppervlakte, kengetal.overige_ruimte_factor, ruimte.naam)
    ]
    if isinstance(ruimte, ZolderRuimte) and not ruimte.heeft_vaste_trap:
        # Beleidsboek 2.2.2.3: zolder zonder vaste trap krijgt een aftrek van
        # 5 punten, gemaximeerd op de waarde van die zolder.
        punten = som(r.punten for r in regels)
        regels.append(
            Regel(
                "Zolder zonder vaste trap",
                -min(AFTREK_ZOLDER_ZONDER_VASTE_TRAP, punten),
                ruimte=ruimte.naam,
            )
        )
    return regels
