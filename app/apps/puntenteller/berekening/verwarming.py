from apps.puntenteller.berekening.helpers import eigen_ruimte, regel
from apps.puntenteller.models import Kengetal
from apps.puntenteller.resultaat import Regel, Rubriek
from apps.puntenteller.ruimte_types import Ruimten, VertrekRuimte


def verwarming_en_verkoeling_rubriek(ruimten: Ruimten, kengetal: Kengetal) -> Rubriek:
    # Beleidsboek 2.3: rubriek 3 verwarming en verkoeling.
    return Rubriek(
        "Verwarming en verkoeling",
        [
            *_verwarming_regels(ruimten, kengetal),
            *_verkoeling_regels(ruimten, kengetal),
        ],
    )


def _verwarming_regels(ruimten: Ruimten, kengetal: Kengetal) -> list[Regel]:
    # Beleidsboek 2.3.1: verwarmde vertrekken krijgen 2 punten per vertrek.
    # Verwarmde overige ruimten en verkeersruimten krijgen 1 punt per ruimte,
    # samen gemaximeerd op vier punten.
    regels = []
    verwarmde_vertrekken = sum(
        1 for r in ruimten.vertrekken if r.verwarmd and eigen_ruimte(r)
    )
    if verwarmde_vertrekken:
        regels.append(
            regel(
                "Verwarmde vertrekken",
                verwarmde_vertrekken,
                kengetal.verwarming_aantal_vertrekken_factor,
            )
        )
    verwarmde_overige_ruimten = sum(
        1
        for r in [*ruimten.overige_ruimten, *ruimten.verkeersruimten]
        if r.verwarmd and eigen_ruimte(r)
    )
    if verwarmde_overige_ruimten:
        maximum = kengetal.verwarming_aantal_overige_ruimten_max
        regels.append(
            regel(
                f"Verwarmde overige ruimten en verkeersruimten (maximaal {maximum})",
                min(verwarmde_overige_ruimten, maximum),
                kengetal.verwarming_aantal_overige_ruimten_factor,
            )
        )
    return regels


def _verkoeling_regels(ruimten: Ruimten, kengetal: Kengetal) -> list[Regel]:
    # Beleidsboek 2.3.3: alleen vertrekken met zowel een verwarmings- als
    # verkoelingsfunctie tellen mee, tot maximaal twee punten.
    regels = []
    verkoelde_vertrekken = sum(
        1 for r in ruimten.vertrekken if r.verwarmd and r.gekoeld and eigen_ruimte(r)
    )
    if verkoelde_vertrekken:
        maximum = kengetal.verkoeling_aantal_vertrekken_max
        regels.append(
            regel(
                f"Verwarmde en gekoelde vertrekken (maximaal {maximum})",
                min(verkoelde_vertrekken, maximum),
                kengetal.verkoeling_aantal_vertrekken_factor,
            )
        )
    return regels


def verwarming_regels_per_ruimte(ruimte, kengetal: Kengetal) -> list[Regel]:
    # Voor rubriek 9: verwarming en verkoeling van één gedeelde ruimte.
    if not ruimte.verwarmd:
        return []
    if not isinstance(ruimte, VertrekRuimte):
        return [
            regel(
                "Verwarmde ruimte",
                1,
                kengetal.verwarming_aantal_overige_ruimten_factor,
                ruimte.naam,
            )
        ]
    regels = [
        regel(
            "Verwarmd vertrek",
            1,
            kengetal.verwarming_aantal_vertrekken_factor,
            ruimte.naam,
        )
    ]
    if ruimte.gekoeld:
        regels.append(
            regel(
                "Gekoeld vertrek",
                1,
                kengetal.verkoeling_aantal_vertrekken_factor,
                ruimte.naam,
            )
        )
    return regels
