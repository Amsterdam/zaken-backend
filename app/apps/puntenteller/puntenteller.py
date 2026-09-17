from decimal import ROUND_DOWN, ROUND_HALF_UP, Decimal
from typing import TYPE_CHECKING

from apps.puntenteller.models import Kengetal, RuimteNaam
from apps.puntenteller.resultaat import (
    PuntentellerResultaat,
    WozBerekening,
    WozCapBerekening,
)
from apps.puntenteller.ruimte_types import (
    BadkamerRuimte,
    KeukenRuimte,
    OverigeRuimte,
    VerkeersRuimte,
    ZolderRuimte,
    maak_overige_ruimte,
    maak_verkeersruimte,
    maak_vertrek_ruimte,
)

if TYPE_CHECKING:
    from apps.puntenteller.models import Gebruikersinvoer


WOZ_CAP_PERCENTAGE = Decimal("0.33")


class Puntenteller:
    gebruikersinvoer: "Gebruikersinvoer"
    kengetal: Kengetal

    def __init__(self, gebruikersinvoer: "Gebruikersinvoer"):
        self.gebruikersinvoer = gebruikersinvoer
        self.kengetal = Kengetal.objects.first()
        if not self.kengetal:
            raise Kengetal.DoesNotExist("Geen kengetal configuratie gevonden")

    def bereken(self):
        return self.bereken_resultaat().totaal_punten_na_caps

    def bereken_resultaat(self) -> PuntentellerResultaat:
        rubrieken_decimal = self._rubriek_totalen()
        woz_berekening = self._woz_berekening()
        woz_cap_berekening = self._woz_cap_berekening(rubrieken_decimal, woz_berekening)
        totaal_bruto = sum(rubrieken_decimal.values(), Decimal("0"))
        return PuntentellerResultaat(
            rubrieken={
                naam: float(waarde) for naam, waarde in rubrieken_decimal.items()
            },
            totaal_punten_bruto=float(totaal_bruto),
            correcties={
                "woz_cap_toegepast": woz_cap_berekening.toegepast,
                "woz_cap_reden": woz_cap_berekening.reden,
                "woz_voor_cap": float(woz_cap_berekening.woz_voor_cap),
                "totaal_zonder_woz": float(
                    totaal_bruto - rubrieken_decimal.get("woz", Decimal("0"))
                ),
                "woz_na_cap": float(woz_cap_berekening.woz_na_cap),
                "woz_cap_uitgesloten": woz_cap_berekening.cap_uitgesloten,
                "woz_cap_uitsluiting_reden": woz_cap_berekening.cap_uitsluiting_reden,
                "woz_minimale_waardering_186_toegepast": (
                    woz_cap_berekening.minimale_waardering_186_toegepast
                ),
            },
            totaal_punten_na_caps=float(woz_cap_berekening.totaal_na_woz_correcties),
        )

    def _rubriek_totalen(self) -> dict[str, Decimal]:
        # Beleidsboek zelfstandige woonruimte januari 2026, hoofdstuk 2:
        # de puntentelling wordt opgebouwd uit rubrieken die daarna samen het totaal vormen.
        return {
            "sanitair": self._badkamer_punten() + self._apart_toilet_punten(),
            "keuken": self._keuken_punten(),
            "vertrekken": self._vertrekken_punten(),
            "overige_ruimten": self._overige_ruimten_punten(),
            "verwarming": self._verwarming_punten(),
            "verkoeling": self._verkoeling_punten(),
            "buitenruimte": self._buitenruimte_punten(),
            "parkeren": self._parkeerruimte_punten(),
            "woz": self._woz_berekening().punten,
            "bijzondere_voorzieningen": self._bijzondere_voorzieningen_punten(),
        }

    def _badkamer_punten(self):
        # Beleidsboek 2.6.1 en 2.6.2: sanitair in badkamer en extra sanitaire voorzieningen.
        return sum(
            (
                self._badkamer_punten_per_ruimte(badkamer)
                for badkamer in self._badkamer_ruimten()
            ),
            Decimal("0"),
        )

    def _keuken_punten(self):
        # Beleidsboek 2.5.3: extra keukenvoorzieningen worden gewaardeerd naast het aanrecht.
        # De cap op extra keukenpunten is nog niet geïmplementeerd.
        return sum(
            (
                self._keuken_punten_per_ruimte(keuken)
                for keuken in self._keuken_ruimten()
            ),
            Decimal("0"),
        )

    def _keuken_aanrecht_punten(self, keuken: KeukenRuimte):
        # Beleidsboek 2.5.2: aanrechtlengte bepaalt de basispunten voor de keuken.
        # Let op: deze staffel volgt nog niet volledig de versie januari 2026 van het beleidsboek.
        meters = keuken.aanrechtlengte_meters or Decimal("0")
        if meters < self.kengetal.keuken_aanrecht_grens_1:
            return self.kengetal.keuken_aanrecht_punten_1
        if meters < self.kengetal.keuken_aanrecht_grens_2:
            return self.kengetal.keuken_aanrecht_punten_2
        if meters < self.kengetal.keuken_aanrecht_grens_3:
            return self.kengetal.keuken_aanrecht_punten_3
        if meters <= self.kengetal.keuken_aanrecht_grens_4:
            return self.kengetal.keuken_aanrecht_punten_4
        return self.kengetal.keuken_aanrecht_punten_5

    def _apart_toilet_punten(self):
        # Beleidsboek 2.6.1: apart toilet in toiletruimte wordt los van badkamer gewaardeerd.
        totaal = Decimal("0")
        totaal += (
            self._waarde(self.gebruikersinvoer.apart_toilet_staand)
            * self.kengetal.apart_toilet_staand_factor
        )
        totaal += (
            self._waarde(self.gebruikersinvoer.apart_toilet_hangend)
            * self.kengetal.apart_toilet_hangend_factor
        )
        return totaal

    def _vertrekken_punten(self):
        # Beleidsboek hoofdstuk 2, rubriek 1 en paragraaf 2.2:
        # vertrekken tellen mee tegen 1 punt per m2 op basis van de lijst met
        # vertrekobjecten met naam en oppervlakte.
        return Decimal(str(self._vertrekken_berekening()["totaal"]))

    def _overige_ruimten_punten(self):
        # Beleidsboek hoofdstuk 2, rubriek 2 en paragraaf 2.2:
        # overige ruimten tellen mee tegen 0,75 punt per m2 op basis van de lijst
        # met objecten met naam en oppervlakte.
        return Decimal(str(self._overige_ruimten_berekening()["totaal"]))

    def _verwarming_punten(self):
        # Beleidsboek 2.3.1: verwarmde vertrekken krijgen 2 punten per vertrek.
        # Verwarmde overige ruimten en verkeersruimten krijgen 1 punt per ruimte,
        # samen gemaximeerd op vier punten.
        verwarmde_vertrekken = sum(
            1 for ruimte in self._vertrek_ruimten() if ruimte.verwarmd
        )
        verwarmde_overige_en_verkeersruimten = sum(
            1 for ruimte in self._overige_ruimten() if ruimte.verwarmd
        ) + sum(1 for ruimte in self._verkeersruimten() if ruimte.verwarmd)

        totaal = (
            Decimal(verwarmde_vertrekken)
            * self.kengetal.verwarming_aantal_vertrekken_factor
        )
        totaal += (
            Decimal(
                min(
                    verwarmde_overige_en_verkeersruimten,
                    self.kengetal.verwarming_aantal_overige_ruimten_max,
                )
            )
            * self.kengetal.verwarming_aantal_overige_ruimten_factor
        )
        return totaal

    def _verkoeling_punten(self):
        # Beleidsboek 2.3.3: alleen vertrekken met zowel een verwarmings-
        # als verkoelingsfunctie tellen mee, tot maximaal twee punten.
        return (
            Decimal(
                min(
                    sum(
                        1
                        for ruimte in self._vertrek_ruimten()
                        if ruimte.verwarmd and ruimte.gekoeld
                    ),
                    self.kengetal.verkoeling_aantal_vertrekken_max,
                )
            )
            * self.kengetal.verkoeling_aantal_vertrekken_factor
        )

    def _buitenruimte_punten(self):
        # Beleidsboek 2.8: buitenruimte wordt gewaardeerd in een aparte rubriek.
        # Let op: deze implementatie gebruikt nog niet de januari 2026 m2-systematiek.
        totaal = Decimal("0")
        totaal += (
            self._waarde(self.gebruikersinvoer.buitenruimte_prive_buitenruimte)
            * self.kengetal.buitenruimte_prive_buitenruimte_factor
        )
        totaal += (
            self._waarde(
                self.gebruikersinvoer.buitenruimte_gemeenschappelijke_buitenruimte
            )
            * self.kengetal.buitenruimte_gemeenschappelijke_buitenruimte_factor
        )
        if (
            self._aantal_of_nul(
                self.gebruikersinvoer.buitenruimte_gemeenschappelijke_buitenruimte
            )
            == 0
        ):
            totaal -= self.kengetal.buitenruimte_geen_gemeenschappelijke_aftrek
        return totaal

    def _parkeerruimte_punten(self):
        # Beleidsboek 2.10.3: gemeenschappelijke parkeerplekken hebben drie typen met vaste waardes.
        # Let op: deling door adressen met gebruiksrecht ontbreekt hier nog.
        totaal = Decimal("0")
        totaal += (
            self._waarde(
                self.gebruikersinvoer.parkeerruimte_gesloten_garage_bij_complex
            )
            * self.kengetal.parkeerruimte_gesloten_garage_bij_complex_factor
        )
        totaal += (
            self._waarde(self.gebruikersinvoer.parkeerruimte_buiten_bij_complex_met_dak)
            * self.kengetal.parkeerruimte_buiten_bij_complex_met_dak_factor
        )
        totaal += (
            self._waarde(
                self.gebruikersinvoer.parkeerruimte_buiten_bij_complex_zonder_dak
            )
            * self.kengetal.parkeerruimte_buiten_bij_complex_zonder_dak_factor
        )
        return totaal

    # Beleidsboek 2.11.2: WOZ-punten bestaan uit onderdeel I en onderdeel II,
    # met kengetallen per waardepeildatum.
    def _woz_punten(self):
        return self._woz_berekening().punten

    def _woz_berekening(self) -> WozBerekening:
        # Beleidsboek 2.11.2 en 2.11.4:
        # onderdeel II rekent met m2 van vertrekken, overige ruimten en type I parkeren.
        woz_peildatum_jaar = self._aantal_of_nul(
            self.gebruikersinvoer.woz_peildatum_jaar
        )
        woz_waarde = self._aantal_of_nul(self.gebruikersinvoer.woz_waarde)
        bouwvoltooiingspercentage = self._decimaal_of_none(
            self.gebruikersinvoer.woz_bouwvoltooiingspercentage
        )
        woz_waarde_na_bouwcorrectie = self._woz_waarde_na_bouwcorrectie(
            woz_waarde, bouwvoltooiingspercentage
        )
        kleine_nieuwbouwwoning = self.gebruikersinvoer.woz_kleine_nieuwbouwwoning
        nieuwbouw_2015_2019 = self.gebruikersinvoer.woz_nieuwbouw_2015_2019
        oppervlakte_vertrekken = Decimal(
            str(self._vertrekken_berekening()["oppervlakte"])
        )
        oppervlakte_overige_ruimten = Decimal(
            str(self._overige_ruimten_berekening()["oppervlakte"])
        )
        oppervlakte_parkeer_type_1 = Decimal(
            self._aantal_of_nul(
                self.gebruikersinvoer.parkeerruimte_gesloten_garage_bij_complex
            )
            * 12
        )
        oppervlakte_totaal = (
            oppervlakte_vertrekken
            + oppervlakte_overige_ruimten
            + oppervlakte_parkeer_type_1
        )
        # Beleidsboek 2.11.2: de relevante oppervlakte wordt eerst afgerond op hele m2.
        oppervlakte_totaal_afgerond = self._afronden_op_hele_m2(oppervlakte_totaal)
        kengetallen = self._woz_kengetallen_per_peiljaar().get(woz_peildatum_jaar)

        if kengetallen is None:
            return WozBerekening(
                punten=Decimal("0"),
                woz_bron="beschikking",
                woz_peildatum_jaar=woz_peildatum_jaar,
                woz_waarde=woz_waarde,
                woz_waarde_na_bouwcorrectie=woz_waarde_na_bouwcorrectie,
                bouwvoltooiingspercentage=bouwvoltooiingspercentage,
                oppervlakte_vertrekken=oppervlakte_vertrekken,
                oppervlakte_overige_ruimten=oppervlakte_overige_ruimten,
                oppervlakte_parkeer_type_1=oppervlakte_parkeer_type_1,
                oppervlakte_totaal_afgerond=oppervlakte_totaal_afgerond,
                kengetal_onderdeel_1=None,
                kengetal_onderdeel_2=None,
                gebruikt_klein_nieuwbouwkengetal=False,
                nieuwbouw_2015_2019_minimum_toegepast=False,
                onderdeel_1_punten=Decimal("0"),
                onderdeel_2_punten=Decimal("0"),
                categorie="onbekend_peiljaar",
            )

        if woz_waarde_na_bouwcorrectie <= 0 or oppervlakte_totaal_afgerond <= 0:
            return WozBerekening(
                punten=Decimal("0"),
                woz_bron="beschikking",
                woz_peildatum_jaar=woz_peildatum_jaar,
                woz_waarde=woz_waarde,
                woz_waarde_na_bouwcorrectie=woz_waarde_na_bouwcorrectie,
                bouwvoltooiingspercentage=bouwvoltooiingspercentage,
                oppervlakte_vertrekken=oppervlakte_vertrekken,
                oppervlakte_overige_ruimten=oppervlakte_overige_ruimten,
                oppervlakte_parkeer_type_1=oppervlakte_parkeer_type_1,
                oppervlakte_totaal_afgerond=oppervlakte_totaal_afgerond,
                kengetal_onderdeel_1=kengetallen["onderdeel_1"],
                kengetal_onderdeel_2=kengetallen["onderdeel_2"],
                gebruikt_klein_nieuwbouwkengetal=False,
                nieuwbouw_2015_2019_minimum_toegepast=False,
                onderdeel_1_punten=Decimal("0"),
                onderdeel_2_punten=Decimal("0"),
                categorie="geen_woz_of_oppervlakte",
            )

        gebruikt_klein_nieuwbouwkengetal = (
            kleine_nieuwbouwwoning
            and "onderdeel_2_kleine_nieuwbouwwoning" in kengetallen
        )
        onderdeel_2_kengetal_sleutel = (
            "onderdeel_2_kleine_nieuwbouwwoning"
            if gebruikt_klein_nieuwbouwkengetal
            else "onderdeel_2"
        )

        # Beleidsboek 2.11.2: onderdeel I is 1 punt per bedrag aan WOZ-waarde.
        onderdeel_1_punten = woz_waarde_na_bouwcorrectie / kengetallen["onderdeel_1"]
        # Beleidsboek 2.11.2 en 2.11.6: onderdeel II is WOZ gedeeld door relevante m2 en daarna
        # door het tweede kengetal. Kleine nieuwbouwwoningen in COROP Amsterdam/Utrecht
        # gebruiken daarvoor een afwijkend onderdeel-II-kengetal.
        onderdeel_2_punten = woz_waarde_na_bouwcorrectie / (
            Decimal(oppervlakte_totaal_afgerond)
            * kengetallen[onderdeel_2_kengetal_sleutel]
        )
        # Beleidsboek 2.11.2 in samenhang met de afrondingsinstructie: totaal wordt afgerond op een kwart punt.
        totaal_punten = self._afronden_op_kwart_punt(
            onderdeel_1_punten + onderdeel_2_punten
        )
        minimum_40_punten_toegepast = False
        if nieuwbouw_2015_2019 and totaal_punten < Decimal("40"):
            # Beleidsboek 2.11.5: voor deze nieuwbouwuitzondering geldt minimaal 40 WOZ-punten.
            totaal_punten = Decimal("40")
            minimum_40_punten_toegepast = True

        return WozBerekening(
            punten=totaal_punten,
            woz_bron="beschikking",
            woz_peildatum_jaar=woz_peildatum_jaar,
            woz_waarde=woz_waarde,
            woz_waarde_na_bouwcorrectie=woz_waarde_na_bouwcorrectie,
            bouwvoltooiingspercentage=bouwvoltooiingspercentage,
            oppervlakte_vertrekken=oppervlakte_vertrekken,
            oppervlakte_overige_ruimten=oppervlakte_overige_ruimten,
            oppervlakte_parkeer_type_1=oppervlakte_parkeer_type_1,
            oppervlakte_totaal_afgerond=oppervlakte_totaal_afgerond,
            kengetal_onderdeel_1=kengetallen["onderdeel_1"],
            kengetal_onderdeel_2=kengetallen[onderdeel_2_kengetal_sleutel],
            gebruikt_klein_nieuwbouwkengetal=gebruikt_klein_nieuwbouwkengetal,
            nieuwbouw_2015_2019_minimum_toegepast=minimum_40_punten_toegepast,
            onderdeel_1_punten=onderdeel_1_punten,
            onderdeel_2_punten=onderdeel_2_punten,
            categorie=(
                "onderdeel_i_en_ii_kleine_nieuwbouwwoning"
                if gebruikt_klein_nieuwbouwkengetal
                else "onderdeel_i_en_ii"
            ),
        )

    def _woz_cap_berekening(
        self,
        rubrieken_decimal: dict[str, Decimal],
        woz_berekening: WozBerekening,
    ) -> WozCapBerekening:
        # Beleidsboek 2.11.2 en 2.11.7: WOZ mag maximaal 33% van het totale puntenaantal vormen.
        woz_punten = rubrieken_decimal["woz"]
        overige_punten = sum(
            waarde for naam, waarde in rubrieken_decimal.items() if naam != "woz"
        )
        totaal_voor_cap = overige_punten + woz_punten
        if woz_punten <= 0 or overige_punten <= 0:
            return WozCapBerekening(
                toegepast=False,
                reden=None,
                woz_voor_cap=woz_punten,
                woz_na_cap=woz_punten,
                maximum_toegestaan=None,
                cap_uitgesloten=False,
                cap_uitsluiting_reden=None,
                totaal_voor_cap=totaal_voor_cap,
                totaal_na_cap=totaal_voor_cap,
                minimale_waardering_186_toegepast=False,
                totaal_na_woz_correcties=totaal_voor_cap,
            )

        if self.gebruikersinvoer.woz_nieuwbouw_2015_2019:
            # Beleidsboek 2.11.5 en 2.11.7: bij nieuwbouw 2015-2019 met de 40-puntenregel
            # is de WOZ-cap rekenkundig niet van toepassing.
            return WozCapBerekening(
                toegepast=False,
                reden=None,
                woz_voor_cap=woz_punten,
                woz_na_cap=woz_punten,
                maximum_toegestaan=None,
                cap_uitgesloten=True,
                cap_uitsluiting_reden="nieuwbouw_2015_2019",
                totaal_voor_cap=totaal_voor_cap,
                totaal_na_cap=totaal_voor_cap,
                minimale_waardering_186_toegepast=False,
                totaal_na_woz_correcties=totaal_voor_cap,
            )

        # Beleidsboek 2.11.7: WOZ mag maximaal 33% van het totaal vormen.
        # Omgerekend naar een maximum op basis van alleen de overige punten is dat:
        # max_woz = (33% / 67%) * overige_punten.
        maximum_toegestaan = self._maximum_woz_bij_cap(overige_punten)
        if woz_punten <= maximum_toegestaan:
            return WozCapBerekening(
                toegepast=False,
                reden=None,
                woz_voor_cap=woz_punten,
                woz_na_cap=woz_punten,
                maximum_toegestaan=maximum_toegestaan,
                cap_uitgesloten=False,
                cap_uitsluiting_reden=None,
                totaal_voor_cap=totaal_voor_cap,
                totaal_na_cap=totaal_voor_cap,
                minimale_waardering_186_toegepast=False,
                totaal_na_woz_correcties=totaal_voor_cap,
            )

        woz_na_cap = self._afronden_naar_beneden_op_hele_punten(maximum_toegestaan)
        totaal_na_cap = totaal_voor_cap - woz_punten + woz_na_cap
        minimale_waardering_186_toegepast = (
            totaal_voor_cap >= Decimal("187")
            and totaal_na_cap < Decimal("187")
            and not woz_berekening.gebruikt_klein_nieuwbouwkengetal
        )
        return WozCapBerekening(
            toegepast=True,
            reden="33_procent_regel",
            woz_voor_cap=woz_punten,
            woz_na_cap=woz_na_cap,
            maximum_toegestaan=maximum_toegestaan,
            cap_uitgesloten=False,
            cap_uitsluiting_reden=None,
            totaal_voor_cap=totaal_voor_cap,
            totaal_na_cap=totaal_na_cap,
            minimale_waardering_186_toegepast=minimale_waardering_186_toegepast,
            totaal_na_woz_correcties=(
                Decimal("186") if minimale_waardering_186_toegepast else totaal_na_cap
            ),
        )

    def _bijzondere_voorzieningen_punten(self):
        # Beleidsboek 2.12.2 en 2.12.3: aanbelfunctie met video/audio en laadpaal.
        # Let op: de huidige puntwaardes zijn nog niet volledig gelijkgetrokken met januari 2026.
        totaal = Decimal("0")
        totaal += (
            self._waarde(
                self.gebruikersinvoer.bijzondere_voorziening_intercom_met_beeld
            )
            * self.kengetal.bijzondere_voorziening_intercom_met_beeld_factor
        )
        totaal += (
            self._waarde(self.gebruikersinvoer.bijzondere_voorziening_laadpaal)
            * self.kengetal.bijzondere_voorziening_laadpaal_factor
        )
        return totaal

    def _waarde(self, waarde: Decimal | int | None) -> Decimal:
        return Decimal(str(waarde or 0))

    def _som_van_ruimten(self, ruimten: list[dict] | None, factor: Decimal) -> Decimal:
        totaal = Decimal("0")
        for ruimte in ruimten or []:
            totaal += self._ruimte_oppervlakte(ruimte) * factor
        return totaal

    def _vertrekken_berekening(self) -> dict[str, float | list[dict] | str]:
        # Beleidsboek hoofdstuk 2, rubriek 1 en paragraaf 2.2:
        # de waardering van vertrekken volgt uit de som van de vloeroppervlaktes
        # van de ruimten die door de gebruiker als vertrek zijn opgegeven.
        factor = self.kengetal.vertrekken_factor
        ruimten = [
            maak_vertrek_ruimte(ruimte)
            for ruimte in (self.gebruikersinvoer.vertrekken or [])
        ]
        oppervlakte = sum(
            (ruimte.ruimte_m2 for ruimte in ruimten),
            Decimal("0"),
        )
        oppervlakte_punten = oppervlakte * factor
        totaal = oppervlakte_punten
        return {
            "factor": float(factor),
            "oppervlakte": float(oppervlakte),
            "oppervlakte_punten": float(oppervlakte_punten),
            "ruimten": [ruimte.as_dict() for ruimte in ruimten],
            "ruimten_punten": float(totaal),
            "totaal": float(totaal),
        }

    def _overige_ruimten_berekening(self) -> dict[str, float | list[dict] | str]:
        # Beleidsboek hoofdstuk 2, rubriek 2 en paragrafen 2.2.2.2 t/m 2.2.2.5:
        # overige ruimten moeten begaanbaar zijn, minimaal 2,00 m2 meten en mogen
        # geen vertrek of verkeersruimte zijn. De selectie van overige ruimten komt
        # hier rechtstreeks uit de door de gebruiker ingevulde lijst. Voor zolderruimte zonder vaste trap
        # geldt een aftrek van 5 punten, gemaximeerd op de waarde van die zolder.
        # Loopruimte naar een andere ruimte via zolder telt niet mee in de zolderoppervlakte.
        factor = self.kengetal.overige_ruimte_factor
        ruimten = [
            maak_overige_ruimte(ruimte)
            for ruimte in (self.gebruikersinvoer.overige_ruimten or [])
        ]
        ruimte_berekeningen = [
            self._overige_ruimte_berekening_per_ruimte(ruimte, factor)
            for ruimte in ruimten
        ]
        oppervlakte = sum(
            (ruimte["effectieve_oppervlakte"] for ruimte in ruimte_berekeningen),
            Decimal("0"),
        )
        oppervlakte_punten = sum(
            (ruimte["punten_voor_aftrek"] for ruimte in ruimte_berekeningen),
            Decimal("0"),
        )
        totaal = sum(
            (ruimte["punten_na_aftrek"] for ruimte in ruimte_berekeningen),
            Decimal("0"),
        )
        return {
            "bron": "beleidsboek hoofdstuk 2, rubriek 2, paragraaf 2.2",
            "factor": float(factor),
            "oppervlakte": float(oppervlakte),
            "oppervlakte_punten": float(oppervlakte_punten),
            "ruimten": [
                self._serialiseer_overige_ruimte_berekening(ruimte)
                for ruimte in ruimte_berekeningen
            ],
            "ruimten_punten": float(totaal),
            "totaal": float(totaal),
        }

    def _som_oppervlakten(self, ruimten: list[dict] | None) -> Decimal:
        totaal = Decimal("0")
        for ruimte in ruimten or []:
            totaal += self._ruimte_oppervlakte(ruimte)
        return totaal

    def _overige_ruimte_berekening_per_ruimte(
        self, ruimte: OverigeRuimte, factor: Decimal
    ) -> dict[str, Decimal | str | bool | None]:
        naam = ruimte.naam
        oppervlakte = ruimte.ruimte_m2
        loopruimte_aftrek = self._zolder_loopruimte_aftrek(ruimte)
        effectieve_oppervlakte = max(oppervlakte - loopruimte_aftrek, Decimal("0"))
        vloer_begaanbaar = ruimte.vloer_begaanbaar
        is_zolderruimte = isinstance(ruimte, ZolderRuimte)
        heeft_vaste_trap = self._zolder_heeft_vaste_trap(ruimte)
        is_prive_parkeerruimte = naam == RuimteNaam.PRIVE_PARKEERRUIMTE

        uitsluiting_reden = None
        if not vloer_begaanbaar:
            # Beleidsboek 2.2.2.2 lid 1.
            uitsluiting_reden = "vloer_niet_begaanbaar"
        elif effectieve_oppervlakte < Decimal("2.00"):
            # Beleidsboek 2.2.2.2 lid 2 en 2.2.2.4.
            uitsluiting_reden = "oppervlakte_kleiner_dan_2m2"

        punten_voor_aftrek = Decimal("0")
        aftrek_zolder_zonder_vaste_trap = Decimal("0")
        punten_na_aftrek = Decimal("0")
        if uitsluiting_reden is None:
            punten_voor_aftrek = effectieve_oppervlakte * factor
            if is_zolderruimte and not heeft_vaste_trap:
                # Beleidsboek 2.2.2.3.
                aftrek_zolder_zonder_vaste_trap = min(Decimal("5"), punten_voor_aftrek)
            punten_na_aftrek = max(
                punten_voor_aftrek - aftrek_zolder_zonder_vaste_trap,
                Decimal("0"),
            )

        return {
            "naam": naam,
            "ruimte_m2": oppervlakte,
            "loopruimte_aftrek_m2": loopruimte_aftrek,
            "effectieve_oppervlakte": (
                effectieve_oppervlakte if uitsluiting_reden is None else Decimal("0")
            ),
            "vloer_begaanbaar": vloer_begaanbaar,
            "is_zolderruimte": is_zolderruimte,
            "heeft_vaste_trap": heeft_vaste_trap,
            "is_prive_parkeerruimte": is_prive_parkeerruimte,
            "uitsluiting_reden": uitsluiting_reden,
            "punten_voor_aftrek": punten_voor_aftrek,
            "aftrek_zolder_zonder_vaste_trap": aftrek_zolder_zonder_vaste_trap,
            "punten_na_aftrek": punten_na_aftrek,
        }

    def _serialiseer_overige_ruimte_berekening(
        self, ruimte: dict[str, Decimal | str | bool | None]
    ) -> dict[str, float | str | bool | None]:
        return {
            "naam": ruimte["naam"],
            "ruimte_m2": float(ruimte["ruimte_m2"]),
            "loopruimte_aftrek_m2": float(ruimte["loopruimte_aftrek_m2"]),
            "effectieve_oppervlakte": float(ruimte["effectieve_oppervlakte"]),
            "vloer_begaanbaar": ruimte["vloer_begaanbaar"],
            "is_zolderruimte": ruimte["is_zolderruimte"],
            "heeft_vaste_trap": ruimte["heeft_vaste_trap"],
            "is_prive_parkeerruimte": ruimte["is_prive_parkeerruimte"],
            "uitsluiting_reden": ruimte["uitsluiting_reden"],
            "punten_voor_aftrek": float(ruimte["punten_voor_aftrek"]),
            "aftrek_zolder_zonder_vaste_trap": float(
                ruimte["aftrek_zolder_zonder_vaste_trap"]
            ),
            "punten_na_aftrek": float(ruimte["punten_na_aftrek"]),
        }

    def _ruimte_oppervlakte(self, ruimte: dict | None) -> Decimal:
        if not isinstance(ruimte, dict):
            return Decimal("0")
        return self._waarde(ruimte.get("ruimte_m2"))

    def _ruimte_naam(self, ruimte: dict | None) -> str:
        if not isinstance(ruimte, dict):
            return "onbekende_ruimte"
        return str(ruimte.get("naam") or "onbekende_ruimte")

    def _ruimte_is_zolderruimte(self, ruimte: dict | None) -> bool:
        return self._ruimte_naam(ruimte) == RuimteNaam.ZOLDER

    def _ruimte_is_prive_parkeerruimte(self, ruimte: dict | None) -> bool:
        return self._ruimte_naam(ruimte) == RuimteNaam.PRIVE_PARKEERRUIMTE

    def _badkamer_ruimten(self) -> list[BadkamerRuimte]:
        return [
            vertrek
            for vertrek in self._vertrek_ruimten()
            if isinstance(vertrek, BadkamerRuimte)
        ]

    def _badkamer_punten_per_ruimte(self, badkamer: BadkamerRuimte) -> Decimal:
        subtotal = Decimal("0")
        subtotal += (
            self._waarde(badkamer.toilet_hangend)
            * self.kengetal.badkamer_toilet_hangend_factor
        )
        subtotal += (
            self._waarde(badkamer.toilet_normaal)
            * self.kengetal.badkamer_toilet_normaal_factor
        )
        subtotal += (
            self._waarde(badkamer.wastafel) * self.kengetal.badkamer_wastafel_factor
        )
        subtotal += (
            self._waarde(badkamer.meerpersoons_wastafel)
            * self.kengetal.badkamer_meerpersoons_wastafel_factor
        )
        subtotal += self._waarde(badkamer.douche) * self.kengetal.badkamer_douche_factor
        subtotal += self._waarde(badkamer.bad) * self.kengetal.badkamer_bad_factor
        subtotal += (
            self._waarde(badkamer.baddouche) * self.kengetal.badkamer_baddouche_factor
        )
        subtotal += (
            self._waarde(badkamer.bubbelfunctie_bad)
            * self.kengetal.badkamer_bubbelfunctie_bad_factor
        )
        subtotal += (
            self._waarde(badkamer.volledige_afscheiding_douche)
            * self.kengetal.badkamer_volledige_afscheiding_douche_factor
        )
        subtotal += (
            self._waarde(badkamer.handdoekenradiator)
            * self.kengetal.badkamer_handdoekenradiator_factor
        )
        subtotal += (
            self._waarde(badkamer.kast_bij_wastafel)
            * self.kengetal.badkamer_kast_bij_wastafel_factor
        )
        subtotal += (
            self._waarde(badkamer.kastruimte) * self.kengetal.badkamer_kastruimte_factor
        )
        subtotal += (
            Decimal(
                min(
                    self._aantal_of_nul(badkamer.stopcontacten),
                    self.kengetal.badkamer_stopcontacten_max,
                )
            )
            * self.kengetal.badkamer_stopcontacten_factor
        )
        subtotal += (
            self._waarde(badkamer.eenhandsmengkraan)
            * self.kengetal.badkamer_eenhandsmengkraan_factor
        )
        subtotal += (
            self._waarde(badkamer.thermostatische_mengkraan)
            * self.kengetal.badkamer_thermostatische_mengkraan_factor
        )
        return subtotal

    def _keuken_ruimten(self) -> list[KeukenRuimte]:
        return [
            vertrek
            for vertrek in self._vertrek_ruimten()
            if isinstance(vertrek, KeukenRuimte)
        ]

    def _keuken_punten_per_ruimte(self, keuken: KeukenRuimte) -> Decimal:
        subtotal = self._keuken_aanrecht_punten(keuken)
        subtotal += (
            self._waarde(keuken.inbouw_afzuiginstallatie)
            * self.kengetal.keuken_inbouw_afzuiginstallatie_factor
        )
        subtotal += (
            self._waarde(keuken.inbouw_kookplaat_inductie)
            * self.kengetal.keuken_inbouw_kookplaat_inductie_factor
        )
        subtotal += (
            self._waarde(keuken.inbouw_kookplaat_keramisch)
            * self.kengetal.keuken_inbouw_kookplaat_keramisch_factor
        )
        subtotal += (
            self._waarde(keuken.inbouw_kookplaat_gas)
            * self.kengetal.keuken_inbouw_kookplaat_gas_factor
        )
        subtotal += (
            self._waarde(keuken.inbouw_koelkast)
            * self.kengetal.keuken_inbouw_koelkast_factor
        )
        subtotal += (
            self._waarde(keuken.inbouw_vrieskast)
            * self.kengetal.keuken_inbouw_vrieskast_factor
        )
        subtotal += (
            self._waarde(keuken.inbouw_oven_elektrisch)
            * self.kengetal.keuken_inbouw_oven_elektrisch_factor
        )
        subtotal += (
            self._waarde(keuken.inbouw_oven_gas)
            * self.kengetal.keuken_inbouw_oven_gas_factor
        )
        subtotal += (
            self._waarde(keuken.inbouw_magnetron)
            * self.kengetal.keuken_inbouw_magnetron_factor
        )
        subtotal += (
            self._waarde(keuken.inbouw_vaatwasmachine)
            * self.kengetal.keuken_inbouw_vaatwasmachine_factor
        )
        subtotal += (
            self._waarde(keuken.extra_kastruimte)
            * self.kengetal.keuken_extra_kastruimte_factor
        )
        subtotal += (
            self._waarde(keuken.eenhandsmengkraan)
            * self.kengetal.keuken_eenhandsmengkraan_factor
        )
        subtotal += (
            self._waarde(keuken.thermostatische_mengkraan)
            * self.kengetal.keuken_thermostatische_mengkraan_factor
        )
        subtotal += (
            self._waarde(keuken.kokendwaterfunctie)
            * self.kengetal.keuken_kokendwaterfunctie_factor
        )
        return subtotal

    def _zolder_loopruimte_aftrek(self, ruimte: OverigeRuimte) -> Decimal:
        if isinstance(ruimte, ZolderRuimte) and ruimte.aftrek_loopruimte_m2 is not None:
            return ruimte.aftrek_loopruimte_m2
        return Decimal("0")

    def _zolder_heeft_vaste_trap(self, ruimte: OverigeRuimte) -> bool:
        if isinstance(ruimte, ZolderRuimte):
            return ruimte.heeft_vaste_trap
        return True

    def _vertrek_ruimten(self) -> list:
        return [
            maak_vertrek_ruimte(ruimte)
            for ruimte in (self.gebruikersinvoer.vertrekken or [])
        ]

    def _overige_ruimten(self) -> list[OverigeRuimte]:
        return [
            maak_overige_ruimte(ruimte)
            for ruimte in (self.gebruikersinvoer.overige_ruimten or [])
        ]

    def _verkeersruimten(self) -> list[VerkeersRuimte]:
        return [
            maak_verkeersruimte(ruimte)
            for ruimte in (self.gebruikersinvoer.verkeersruimten or [])
        ]

    def _ruimte_bool(
        self, ruimte: dict | None, veld: str, default: bool = False
    ) -> bool:
        if not isinstance(ruimte, dict):
            return default
        waarde = ruimte.get(veld, default)
        return bool(waarde)

    def _ruimte_waarde(self, ruimte: dict | None, veld: str):
        if not isinstance(ruimte, dict):
            return None
        return ruimte.get(veld)

    def _decimaal_of_none(self, waarde: Decimal | int | None) -> Decimal | None:
        if waarde is None:
            return None
        return Decimal(str(waarde))

    def _aantal_of_nul(self, aantal: int | None) -> int:
        return aantal or 0

    def _afronden_op_kwart_punt(self, waarde: Decimal) -> Decimal:
        # Beleidsboek afrondingsinstructie: puntentotalen worden in kwartpunten afgerond.
        return (waarde * Decimal("4")).quantize(
            Decimal("1"), rounding=ROUND_HALF_UP
        ) / Decimal("4")

    def _afronden_op_hele_m2(self, waarde: Decimal) -> int:
        # Beleidsboek 2.11.2: bij 0,5 m2 of meer wordt naar boven afgerond, anders naar beneden.
        return int(waarde.quantize(Decimal("1"), rounding=ROUND_HALF_UP))

    def _afronden_naar_beneden_op_hele_punten(self, waarde: Decimal) -> Decimal:
        # Beleidsboek 2.11.2 en 2.11.7: bij toepassing van de WOZ-cap wordt naar beneden op hele punten afgerond.
        return waarde.quantize(Decimal("1"), rounding=ROUND_DOWN)

    def _maximum_woz_bij_cap(self, overige_punten: Decimal) -> Decimal:
        return (
            WOZ_CAP_PERCENTAGE / (Decimal("1") - WOZ_CAP_PERCENTAGE)
        ) * overige_punten

    def _woz_waarde_na_bouwcorrectie(
        self, woz_waarde: int, bouwvoltooiingspercentage: Decimal | None
    ) -> Decimal:
        # Beleidsboek 2.11.4: bij gebouwd eigendom in aanbouw wordt gerekend met de waarde
        # alsof de bouw 100% is voltooid.
        if bouwvoltooiingspercentage is None:
            return self._waarde(woz_waarde)
        if bouwvoltooiingspercentage <= 0 or bouwvoltooiingspercentage >= 100:
            return self._waarde(woz_waarde)
        return self._waarde(woz_waarde) / (bouwvoltooiingspercentage / Decimal("100"))

    def _woz_kengetallen_per_peiljaar(self) -> dict[int, dict[str, Decimal]]:
        # Beleidsboek 2.11.2: de bedragen voor onderdeel I en II verschillen per waardepeildatum.
        return {
            int(peiljaar): {
                "onderdeel_1": Decimal(str(kengetallen["onderdeel_1"])),
                "onderdeel_2": Decimal(str(kengetallen["onderdeel_2"])),
                "onderdeel_2_kleine_nieuwbouwwoning": Decimal(
                    str(kengetallen["onderdeel_2_kleine_nieuwbouwwoning"])
                ),
            }
            for peiljaar, kengetallen in self.kengetal.woz_kengetallen_per_peiljaar.items()
        }
