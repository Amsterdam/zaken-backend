from dataclasses import asdict, dataclass
from decimal import Decimal


@dataclass
class PuntentellerResultaat:
    rubrieken: dict[str, float]
    totaal_punten_bruto: float
    correcties: dict[str, float | bool | str | None]
    totaal_punten_na_caps: float

    def as_dict(self) -> dict:
        return asdict(self)


@dataclass
class WozBerekening:
    punten: Decimal
    woz_bron: str
    woz_peildatum_jaar: int
    woz_waarde: int
    woz_waarde_na_bouwcorrectie: Decimal
    bouwvoltooiingspercentage: Decimal | None
    oppervlakte_vertrekken: Decimal
    oppervlakte_overige_ruimten: Decimal
    oppervlakte_parkeer_type_1: Decimal
    oppervlakte_totaal_afgerond: int
    kengetal_onderdeel_1: Decimal | None
    kengetal_onderdeel_2: Decimal | None
    gebruikt_klein_nieuwbouwkengetal: bool
    nieuwbouw_2015_2019_minimum_toegepast: bool
    onderdeel_1_punten: Decimal
    onderdeel_2_punten: Decimal
    categorie: str

    def as_dict(self) -> dict[str, float | int | str | None]:
        return {
            "punten": float(self.punten),
            "woz_bron": self.woz_bron,
            "woz_peildatum_jaar": self.woz_peildatum_jaar,
            "woz_waarde": self.woz_waarde,
            "woz_waarde_na_bouwcorrectie": float(self.woz_waarde_na_bouwcorrectie),
            "bouwvoltooiingspercentage": (
                None
                if self.bouwvoltooiingspercentage is None
                else float(self.bouwvoltooiingspercentage)
            ),
            "oppervlakte_vertrekken": float(self.oppervlakte_vertrekken),
            "oppervlakte_overige_ruimten": float(self.oppervlakte_overige_ruimten),
            "oppervlakte_parkeer_type_1": float(self.oppervlakte_parkeer_type_1),
            "oppervlakte_totaal_afgerond": self.oppervlakte_totaal_afgerond,
            "kengetal_onderdeel_1": (
                None
                if self.kengetal_onderdeel_1 is None
                else float(self.kengetal_onderdeel_1)
            ),
            "kengetal_onderdeel_2": (
                None
                if self.kengetal_onderdeel_2 is None
                else float(self.kengetal_onderdeel_2)
            ),
            "gebruikt_klein_nieuwbouwkengetal": self.gebruikt_klein_nieuwbouwkengetal,
            "nieuwbouw_2015_2019_minimum_toegepast": self.nieuwbouw_2015_2019_minimum_toegepast,
            "onderdeel_1_punten": float(self.onderdeel_1_punten),
            "onderdeel_2_punten": float(self.onderdeel_2_punten),
            "categorie": self.categorie,
        }


@dataclass
class WozCapBerekening:
    toegepast: bool
    reden: str | None
    woz_voor_cap: Decimal
    woz_na_cap: Decimal
    maximum_toegestaan: Decimal | None
    cap_uitgesloten: bool
    cap_uitsluiting_reden: str | None
    totaal_voor_cap: Decimal
    totaal_na_cap: Decimal
    minimale_waardering_186_toegepast: bool
    totaal_na_woz_correcties: Decimal

    def as_dict(self) -> dict[str, float | bool | str | None]:
        return {
            "toegepast": self.toegepast,
            "reden": self.reden,
            "woz_voor_cap": float(self.woz_voor_cap),
            "woz_na_cap": float(self.woz_na_cap),
            "maximum_toegestaan": (
                None
                if self.maximum_toegestaan is None
                else float(self.maximum_toegestaan)
            ),
            "cap_uitgesloten": self.cap_uitgesloten,
            "cap_uitsluiting_reden": self.cap_uitsluiting_reden,
            "totaal_voor_cap": float(self.totaal_voor_cap),
            "totaal_na_cap": float(self.totaal_na_cap),
            "minimale_waardering_186_toegepast": self.minimale_waardering_186_toegepast,
            "totaal_na_woz_correcties": float(self.totaal_na_woz_correcties),
        }
