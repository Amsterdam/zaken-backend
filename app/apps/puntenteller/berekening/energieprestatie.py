from decimal import Decimal

from apps.puntenteller.berekening.correcties import MONUMENTEN, monument_soort
from apps.puntenteller.berekening.helpers import decimaal_of_none, nl
from apps.puntenteller.models import Gebruikersinvoer, Kengetal
from apps.puntenteller.resultaat import Regel, Rubriek

LABEL_SLEUTELS = {
    "A++++": "a4plus",
    "A+++": "a3plus",
    "A++": "a2plus",
    "A+": "aplus",
    "A": "a",
    "B": "b",
    "C": "c",
    "D": "d",
    "E": "e",
    "F": "f",
    "G": "g",
}


def energieprestatie_rubriek(invoer: Gebruikersinvoer, kengetal: Kengetal) -> Rubriek:
    # Vereenvoudigde energielogica: zonder woningtype geen punten. Daarna gaat
    # EPV voor, dan label, dan energie-index en anders bouwjaar.
    regel = _energieprestatie_regel(invoer, kengetal)
    regels = [regel]
    if monument_soort(invoer) in MONUMENTEN and regel.punten < 0:
        # Beleidsboek 2.4.6.1: rijks-, provinciale en gemeentelijke monumenten
        # krijgen geen minpunten voor rubriek 4.
        regels.append(Regel("Monument: geen minpunten", -regel.punten))
    return Rubriek("Energieprestatie", regels)


def _energieprestatie_regel(invoer: Gebruikersinvoer, kengetal: Kengetal) -> Regel:
    if invoer.is_eengezinswoning is None:
        return Regel("Geen woningtype opgegeven", Decimal("0"))

    woningtype = "eengezinswoning" if invoer.is_eengezinswoning else "meergezinswoning"

    if invoer.heeft_energieprestatievergoeding:
        return Regel(
            f"Energieprestatievergoeding, {woningtype}",
            _kengetal(kengetal, f"energieprestatie_epv_{woningtype}_punten"),
        )

    label = (invoer.energielabel_klasse or "").strip().upper()
    if label:
        sleutel = LABEL_SLEUTELS.get(label)
        if sleutel is None:
            return Regel(f"Onbekend energielabel {label}", Decimal("0"))
        return Regel(
            f"Energielabel {label}, {woningtype}",
            _kengetal(
                kengetal, f"energieprestatie_label_{sleutel}_{woningtype}_punten"
            ),
        )

    energie_index = decimaal_of_none(invoer.energie_index)
    if energie_index is not None:
        band = _energie_index_band(energie_index, kengetal)
        return Regel(
            f"Energie-index {nl(energie_index)}, {woningtype}",
            _kengetal(kengetal, f"energieprestatie_ei_punten_{band}_{woningtype}"),
        )

    bouwjaar = invoer.bouwjaar or 0
    if bouwjaar <= 0:
        return Regel("Geen bouwjaar opgegeven", Decimal("0"))
    band = _bouwjaar_band(bouwjaar, kengetal)
    return Regel(
        f"Bouwjaar {bouwjaar}, {woningtype}",
        _kengetal(kengetal, f"energieprestatie_bouwjaar_punten_{band}_{woningtype}"),
    )


def _energie_index_band(energie_index: Decimal, kengetal: Kengetal) -> int:
    for band in range(1, 9):
        if energie_index <= getattr(kengetal, f"energieprestatie_ei_grens_{band}"):
            return band
    return 9


def _bouwjaar_band(bouwjaar: int, kengetal: Kengetal) -> int:
    for band in range(1, 7):
        if bouwjaar >= getattr(kengetal, f"energieprestatie_bouwjaar_grens_{band}"):
            return band
    return 7


def _kengetal(kengetal: Kengetal, veldnaam: str) -> Decimal:
    return Decimal(str(getattr(kengetal, veldnaam)))
