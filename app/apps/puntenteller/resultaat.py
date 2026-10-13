from dataclasses import dataclass, field
from decimal import ROUND_HALF_UP, Decimal

from apps.puntenteller.models import RuimteNaam

WEERGAVE_PRECISIE = Decimal("0.01")


@dataclass
class Regel:
    omschrijving: str
    punten: Decimal
    ruimte: str | None = None
    aantal: Decimal | int | None = None
    factor: Decimal | None = None
    # Een afrondingsregel brengt het lopende totaal op een afgerond getal.
    afronding: bool = False

    def as_dict(self, punten: Decimal | None = None) -> dict:
        return {
            "omschrijving": self.omschrijving,
            "punten": float(_weergave(self.punten if punten is None else punten)),
            "ruimte": _ruimte_label(self.ruimte),
            "aantal": None if self.aantal is None else float(self.aantal),
            "factor": None if self.factor is None else float(self.factor),
        }


@dataclass
class Rubriek:
    """Een rubriek of opslag. De punten zijn altijd de som van de regels."""

    naam: str
    regels: list[Regel] = field(default_factory=list)

    @property
    def punten(self) -> Decimal:
        return sum((regel.punten for regel in self.regels), Decimal("0"))

    def as_dict(self, weergave: list[Decimal]) -> dict:
        return {
            "naam": self.naam,
            "punten": float(sum(weergave, Decimal("0"))),
            "regels": [
                regel.as_dict(punten)
                for regel, punten in zip(self.regels, weergave)
                if not (regel.afronding and punten == 0)
            ],
        }


@dataclass
class Huurprijsopslag:
    """Een procentuele opslag op de maximale huurprijs, geen punten."""

    naam: str
    procent: Decimal

    def as_dict(self) -> dict:
        return {"naam": self.naam, "procent": float(self.procent)}


@dataclass
class PuntentellerResultaat:
    rubrieken: list[Rubriek]
    opslagen: list[Rubriek]
    huurprijsopslagen: list[Huurprijsopslag] = field(default_factory=list)

    @property
    def totaal_punten(self) -> Decimal:
        return sum(
            (rubriek.punten for rubriek in [*self.rubrieken, *self.opslagen]),
            Decimal("0"),
        )

    def rubriek(self, naam: str) -> Rubriek:
        return next(r for r in [*self.rubrieken, *self.opslagen] if r.naam == naam)

    def as_dict(self) -> dict:
        alle = [*self.rubrieken, *self.opslagen]
        weergave = dict(zip(map(id, alle), _weergave_per_rubriek(alle)))
        return {
            "totaal_punten": float(self.totaal_punten),
            "rubrieken": [r.as_dict(weergave[id(r)]) for r in self.rubrieken],
            "opslagen": [
                r.as_dict(weergave[id(r)])
                for r in self.opslagen
                if any(weergave[id(r)])
            ],
            "huurprijsopslagen": [o.as_dict() for o in self.huurprijsopslagen],
            "huurprijsopslag_procent": float(
                sum((o.procent for o in self.huurprijsopslagen), Decimal("0"))
            ),
        }


def _weergave_per_rubriek(rubrieken: list[Rubriek]) -> list[list[Decimal]]:
    # Er wordt exact gerekend; alleen de weergave wordt op 2 decimalen afgerond.
    # Een afrondingsregel toont het verschil tussen het exacte lopende totaal en
    # wat er tot dan toe getoond is. Zo tellen de getoonde regels altijd op tot
    # de getoonde rubriek en het getoonde totaal.
    exact = getoond = Decimal("0")
    resultaat = []
    for rubriek in rubrieken:
        punten_per_regel = []
        for regel in rubriek.regels:
            exact += regel.punten
            punten = _weergave(exact - getoond if regel.afronding else regel.punten)
            getoond += punten
            punten_per_regel.append(punten)
        resultaat.append(punten_per_regel)
    return resultaat


def _weergave(punten: Decimal) -> Decimal:
    return punten.quantize(WEERGAVE_PRECISIE, rounding=ROUND_HALF_UP)


def _ruimte_label(naam: str | None) -> str | None:
    if naam in RuimteNaam.values:
        return RuimteNaam(naam).label
    return naam
