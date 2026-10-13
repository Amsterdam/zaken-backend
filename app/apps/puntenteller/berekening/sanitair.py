from decimal import Decimal

from apps.puntenteller.berekening.helpers import (
    begrensd,
    eigen_ruimte,
    regel,
    som,
    voorziening_regels,
)
from apps.puntenteller.models import Kengetal
from apps.puntenteller.resultaat import Regel, Rubriek
from apps.puntenteller.ruimte_types import (
    BadkamerRuimte,
    OverigeRuimte,
    Ruimten,
    ToiletRuimte,
    VertrekRuimte,
)

BAD_DOUCHE = ("douche", "bad", "baddouche")
BADKAMER_TOILETTEN = ("toilet_hangend", "toilet_normaal")
BADKAMER_WASTAFELS = ("wastafel", "meerpersoons_wastafel")
# Extra badkamervoorzieningen met een vaste factor per stuk (kengetal badkamer_<veld>_factor).
BADKAMER_EXTRA_VOORZIENINGEN = (
    "bubbelfunctie_bad",
    "volledige_afscheiding_douche",
    "handdoekenradiator",
    "kast_bij_wastafel",
    "eenhandsmengkraan",
    "thermostatische_mengkraan",
)


def sanitair_rubriek(ruimten: Ruimten, kengetal: Kengetal) -> Rubriek:
    # Beleidsboek 2.6: rubriek 6 sanitair, gewaardeerd per ruimte. Sanitair in
    # gedeelde ruimten valt onder rubriek 9.
    return Rubriek(
        "Sanitair",
        [
            r
            for ruimte in [*ruimten.vertrekken, *ruimten.overige_ruimten]
            if eigen_ruimte(ruimte)
            for r in sanitair_regels(ruimte, kengetal)
        ],
    )


def sanitair_regels(
    ruimte: VertrekRuimte | OverigeRuimte, kengetal: Kengetal
) -> list[Regel]:
    if isinstance(ruimte, BadkamerRuimte):
        return _badkamer_regels(ruimte, kengetal)
    if isinstance(ruimte, ToiletRuimte):
        return _toiletruimte_regels(ruimte, kengetal)
    # Beleidsboek 2.6.1: wastafel, meerpersoonswastafel, douche, bad en
    # bad/douche kunnen ook in andere vertrekken en overige ruimten voorkomen.
    return _sanitair_regels(ruimte, kengetal)


def _badkamer_regels(badkamer: BadkamerRuimte, kengetal: Kengetal) -> list[Regel]:
    basis = voorziening_regels(
        badkamer,
        [*BADKAMER_TOILETTEN, *BADKAMER_WASTAFELS, *BAD_DOUCHE],
        kengetal,
        "badkamer",
    )
    extra = _badkamer_extra_regels(badkamer, kengetal)
    if not (badkamer.wastafel or badkamer.meerpersoons_wastafel):
        # Beleidsboek 2.6.2: extra voorzieningen tellen alleen in een ruimte met
        # een wastafel.
        return [
            *basis,
            *begrensd(
                extra,
                Decimal("0"),
                "Geen extra voorzieningen zonder wastafel",
                badkamer.naam,
            ),
        ]
    # Afwijking op beleidsboek 2.6.2: in deze toepassing wordt per badkamer
    # afgetopt op de bad/douchepunten, zodat sanitair in een andere ruimte de
    # cap niet vergroot.
    maximum = som(
        r.punten for r in voorziening_regels(badkamer, BAD_DOUCHE, kengetal, "badkamer")
    )
    extra = begrensd(
        extra,
        maximum,
        "Maximum extra voorzieningen (punten voor douche en bad)",
        badkamer.naam,
    )
    return [*basis, *extra]


def _toiletruimte_regels(toilet: ToiletRuimte, kengetal: Kengetal) -> list[Regel]:
    # Beleidsboek 2.6.1: toilet in een toiletruimte wordt als aparte sanitaire
    # voorziening per toiletruimte gewaardeerd.
    return [
        *voorziening_regels(
            toilet, ("toilet_staand", "toilet_hangend"), kengetal, "apart"
        ),
        *_sanitair_regels(toilet, kengetal),
    ]


def _badkamer_extra_regels(badkamer: BadkamerRuimte, kengetal: Kengetal) -> list[Regel]:
    regels = voorziening_regels(
        badkamer, BADKAMER_EXTRA_VOORZIENINGEN, kengetal, "badkamer"
    )
    if badkamer.kastruimte:
        regels.append(
            regel(
                "Kastruimte (maximaal 1)",
                min(badkamer.kastruimte, 1),
                kengetal.badkamer_kastruimte_factor,
                badkamer.naam,
            )
        )
    if badkamer.stopcontacten:
        # Beleidsboek 2.6.2: maximaal twee stopcontacten per (meerpersoons)wastafel.
        per_wastafel = kengetal.badkamer_stopcontacten_max
        maximum = per_wastafel * (badkamer.wastafel + badkamer.meerpersoons_wastafel)
        regels.append(
            regel(
                f"Stopcontacten (maximaal {per_wastafel} per wastafel)",
                min(badkamer.stopcontacten, maximum),
                kengetal.badkamer_stopcontacten_factor,
                badkamer.naam,
            )
        )
    return regels


def _sanitair_regels(
    ruimte: VertrekRuimte | OverigeRuimte, kengetal: Kengetal
) -> list[Regel]:
    regels = voorziening_regels(ruimte, BAD_DOUCHE, kengetal, "badkamer")
    if ruimte.wastafel > 0:
        # Beleidsboek 2.6.1: wastafel in een vertrek of overige ruimte krijgt
        # maximaal 1 punt per ruimte.
        regels.append(
            Regel(
                "Wastafel (maximaal 1 per ruimte)",
                Decimal(kengetal.sanitair_wastafel_niet_badkamer_max_punten),
                ruimte=ruimte.naam,
            )
        )
    if ruimte.meerpersoons_wastafel > 0:
        # Beleidsboek 2.6.1: meerpersoonswastafel in een vertrek of overige
        # ruimte krijgt maximaal 1,5 punt per ruimte.
        regels.append(
            Regel(
                "Meerpersoons wastafel (maximaal 1 per ruimte)",
                Decimal(
                    kengetal.sanitair_meerpersoons_wastafel_niet_badkamer_max_punten
                ),
                ruimte=ruimte.naam,
            )
        )
    return regels
