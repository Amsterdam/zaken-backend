from decimal import ROUND_DOWN, ROUND_HALF_UP, Decimal
from typing import TYPE_CHECKING

from apps.puntenteller.models import Kengetal
from apps.puntenteller.resultaat import (
    BeleidsContext,
    PuntentellerResultaat,
    WozBerekening,
    WozCapBerekening,
)

if TYPE_CHECKING:
    from apps.puntenteller.models import Gebruikersinvoer


WOZ_CAP_PERCENTAGE = Decimal("0.33")


class Puntenteller:
    gebruikersinvoer: "Gebruikersinvoer"
    kengetal: Kengetal
    beleidscontext: BeleidsContext

    def __init__(
        self,
        gebruikersinvoer: "Gebruikersinvoer",
        beleidscontext: BeleidsContext | None = None,
    ):
        self.gebruikersinvoer = gebruikersinvoer
        self.beleidscontext = beleidscontext or BeleidsContext()
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
                "woz_na_cap": float(woz_cap_berekening.woz_na_cap),
                "woz_cap_uitgesloten": woz_cap_berekening.cap_uitgesloten,
                "woz_cap_uitsluiting_reden": woz_cap_berekening.cap_uitsluiting_reden,
                "woz_minimale_waardering_186_toegepast": (
                    woz_cap_berekening.minimale_waardering_186_toegepast
                ),
            },
            totaal_punten_na_caps=float(woz_cap_berekening.totaal_na_woz_correcties),
            huurprijs_opslagen={},
            toelichting={
                "beleid_context": {
                    "status": "voorbereid_op_gestructureerde_output",
                },
                "woz": woz_berekening.as_dict(),
                "woz_cap": woz_cap_berekening.as_dict(),
            },
            beleid_context=self.beleidscontext.as_dict(),
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
        subtotal = Decimal("0")
        subtotal += (
            self._waarde(self.gebruikersinvoer.badkamer_toilet_hangend)
            * self.kengetal.badkamer_toilet_hangend_factor
        )
        subtotal += (
            self._waarde(self.gebruikersinvoer.badkamer_toilet_normaal)
            * self.kengetal.badkamer_toilet_normaal_factor
        )
        subtotal += (
            self._waarde(self.gebruikersinvoer.badkamer_wastafel)
            * self.kengetal.badkamer_wastafel_factor
        )
        subtotal += (
            self._waarde(self.gebruikersinvoer.badkamer_meerpersoons_wastafel)
            * self.kengetal.badkamer_meerpersoons_wastafel_factor
        )
        subtotal += (
            self._waarde(self.gebruikersinvoer.badkamer_douche)
            * self.kengetal.badkamer_douche_factor
        )
        subtotal += (
            self._waarde(self.gebruikersinvoer.badkamer_bad)
            * self.kengetal.badkamer_bad_factor
        )
        subtotal += (
            self._waarde(self.gebruikersinvoer.badkamer_baddouche)
            * self.kengetal.badkamer_baddouche_factor
        )
        subtotal += (
            self._waarde(self.gebruikersinvoer.badkamer_bubbelfunctie_bad)
            * self.kengetal.badkamer_bubbelfunctie_bad_factor
        )
        subtotal += (
            self._waarde(self.gebruikersinvoer.badkamer_volledige_afscheiding_douche)
            * self.kengetal.badkamer_volledige_afscheiding_douche_factor
        )
        subtotal += (
            self._waarde(self.gebruikersinvoer.badkamer_handdoekenradiator)
            * self.kengetal.badkamer_handdoekenradiator_factor
        )
        subtotal += (
            self._waarde(self.gebruikersinvoer.badkamer_kast_bij_wastafel)
            * self.kengetal.badkamer_kast_bij_wastafel_factor
        )
        subtotal += (
            self._waarde(self.gebruikersinvoer.badkamer_kastruimte)
            * self.kengetal.badkamer_kastruimte_factor
        )
        # Beleidsboek 2.6.2: stopcontacten tellen maximaal twee per
        # (meerpersoons)wastafel mee. De huidige implementatie gebruikt nog een globale cap.
        subtotal += (
            Decimal(
                min(
                    self._aantal_of_nul(self.gebruikersinvoer.badkamer_stopcontacten),
                    self.kengetal.badkamer_stopcontacten_max,
                )
            )
            * self.kengetal.badkamer_stopcontacten_factor
        )
        subtotal += (
            self._waarde(self.gebruikersinvoer.badkamer_eenhandsmengkraan)
            * self.kengetal.badkamer_eenhandsmengkraan_factor
        )
        subtotal += (
            self._waarde(self.gebruikersinvoer.badkamer_thermostatische_mengkraan)
            * self.kengetal.badkamer_thermostatische_mengkraan_factor
        )
        return subtotal * self._waarde(self.gebruikersinvoer.badkamer_aantal_adressen)

    def _keuken_punten(self):
        # Beleidsboek 2.5.3: extra keukenvoorzieningen worden gewaardeerd naast het aanrecht.
        # De cap op extra keukenpunten is nog niet geïmplementeerd.
        subtotal = self._keuken_aanrecht_punten()
        subtotal += (
            self._waarde(self.gebruikersinvoer.keuken_inbouw_afzuiginstallatie)
            * self.kengetal.keuken_inbouw_afzuiginstallatie_factor
        )
        subtotal += (
            self._waarde(self.gebruikersinvoer.keuken_inbouw_kookplaat_inductie)
            * self.kengetal.keuken_inbouw_kookplaat_inductie_factor
        )
        subtotal += (
            self._waarde(self.gebruikersinvoer.keuken_inbouw_kookplaat_keramisch)
            * self.kengetal.keuken_inbouw_kookplaat_keramisch_factor
        )
        subtotal += (
            self._waarde(self.gebruikersinvoer.keuken_inbouw_kookplaat_gas)
            * self.kengetal.keuken_inbouw_kookplaat_gas_factor
        )
        subtotal += (
            self._waarde(self.gebruikersinvoer.keuken_inbouw_koelkast)
            * self.kengetal.keuken_inbouw_koelkast_factor
        )
        subtotal += (
            self._waarde(self.gebruikersinvoer.keuken_inbouw_vrieskast)
            * self.kengetal.keuken_inbouw_vrieskast_factor
        )
        subtotal += (
            self._waarde(self.gebruikersinvoer.keuken_inbouw_oven_elektrisch)
            * self.kengetal.keuken_inbouw_oven_elektrisch_factor
        )
        subtotal += (
            self._waarde(self.gebruikersinvoer.keuken_inbouw_oven_gas)
            * self.kengetal.keuken_inbouw_oven_gas_factor
        )
        subtotal += (
            self._waarde(self.gebruikersinvoer.keuken_inbouw_magnetron)
            * self.kengetal.keuken_inbouw_magnetron_factor
        )
        subtotal += (
            self._waarde(self.gebruikersinvoer.keuken_inbouw_vaatwasmachine)
            * self.kengetal.keuken_inbouw_vaatwasmachine_factor
        )
        subtotal += (
            self._waarde(self.gebruikersinvoer.keuken_extra_kastruimte)
            * self.kengetal.keuken_extra_kastruimte_factor
        )
        subtotal += (
            self._waarde(self.gebruikersinvoer.keuken_eenhandsmengkraan)
            * self.kengetal.keuken_eenhandsmengkraan_factor
        )
        subtotal += (
            self._waarde(self.gebruikersinvoer.keuken_thermostatische_mengkraan)
            * self.kengetal.keuken_thermostatische_mengkraan_factor
        )
        subtotal += (
            self._waarde(self.gebruikersinvoer.keuken_kokendwaterfunctie)
            * self.kengetal.keuken_kokendwaterfunctie_factor
        )
        return subtotal * self._waarde(self.gebruikersinvoer.keuken_aantal_adressen)

    def _keuken_aanrecht_punten(self):
        # Beleidsboek 2.5.2: aanrechtlengte bepaalt de basispunten voor de keuken.
        # Let op: deze staffel volgt nog niet volledig de versie januari 2026 van het beleidsboek.
        meters = self._waarde(self.gebruikersinvoer.keuken_aanrechtlengte_meters)
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
        # Beleidsboek 2.2: vertrekken worden op oppervlakte gewaardeerd.
        factor = self.kengetal.vertrekken_factor
        totaal = self._waarde(self.gebruikersinvoer.vertrekken_oppervlakte) * factor
        totaal += self._waarde(self.gebruikersinvoer.vertrekken_1) * factor
        totaal += self._waarde(self.gebruikersinvoer.vertrekken_2) * factor
        totaal += self._waarde(self.gebruikersinvoer.vertrekken_3) * factor
        totaal += self._waarde(self.gebruikersinvoer.vertrekken_4) * factor
        totaal += self._waarde(self.gebruikersinvoer.vertrekken_5) * factor
        totaal += self._waarde(self.gebruikersinvoer.vertrekken_6) * factor
        return totaal

    def _overige_ruimten_punten(self):
        # Beleidsboek 2.2: overige ruimten hebben een eigen waardering per m2.
        factor = self.kengetal.overige_ruimte_factor
        totaal = self._waarde(self.gebruikersinvoer.overige_ruimte_oppervlakte) * factor
        totaal += self._waarde(self.gebruikersinvoer.overige_ruimte_1) * factor
        totaal += self._waarde(self.gebruikersinvoer.overige_ruimte_2) * factor
        totaal += self._waarde(self.gebruikersinvoer.overige_ruimte_3) * factor
        totaal += self._waarde(self.gebruikersinvoer.overige_ruimte_4) * factor
        totaal += self._waarde(self.gebruikersinvoer.overige_ruimte_5) * factor
        return totaal

    def _verwarming_punten(self):
        # Beleidsboek 2.3.1: verwarming in vertrekken telt mee.
        totaal = (
            self._waarde(self.gebruikersinvoer.verwarming_aantal_vertrekken)
            * self.kengetal.verwarming_aantal_vertrekken_factor
        )
        # Beleidsboek 2.3.1: overige ruimten en verkeersruimten hebben een maximum van vier punten.
        totaal += (
            Decimal(
                min(
                    self._aantal_of_nul(
                        self.gebruikersinvoer.verwarming_aantal_overige_ruimten
                    ),
                    self.kengetal.verwarming_aantal_overige_ruimten_max,
                )
            )
            * self.kengetal.verwarming_aantal_overige_ruimten_factor
        )
        return totaal

    def _verkoeling_punten(self):
        # Beleidsboek 2.3.3: verkoeling telt alleen voor vertrekken mee en maximaal twee punten.
        return (
            Decimal(
                min(
                    self._aantal_of_nul(
                        self.gebruikersinvoer.verkoeling_aantal_vertrekken
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
        oppervlakte_vertrekken = self._waarde(
            self.gebruikersinvoer.vertrekken_oppervlakte
        )
        oppervlakte_overige_ruimten = self._waarde(
            self.gebruikersinvoer.overige_ruimte_oppervlakte
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
