from datetime import date
from decimal import ROUND_DOWN, ROUND_HALF_UP, Decimal
from typing import TYPE_CHECKING

from apps.puntenteller.models import Kengetal, RuimteNaam
from apps.puntenteller.resultaat import (
    EnergieprestatieBerekening,
    PuntentellerResultaat,
    WozBerekening,
    WozCapBerekening,
)
from apps.puntenteller.ruimte_types import (
    BadkamerRuimte,
    GemeenschappelijkeBuitenruimte,
    KeukenRuimte,
    OverigeRuimte,
    PriveBuitenruimte,
    ToiletRuimte,
    VerkeersRuimte,
    VertrekRuimte,
    ZolderRuimte,
    maak_buitenruimte,
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
        energieprestatie_berekening = self._energieprestatie_berekening()
        sanitair_cap_berekening = self._sanitair_extra_voorzieningen_cap_berekening()
        woz_berekening = self._woz_berekening()
        woz_cap_berekening = self._woz_cap_berekening(rubrieken_decimal, woz_berekening)
        totaal_bruto = sum(rubrieken_decimal.values(), Decimal("0"))
        return PuntentellerResultaat(
            rubrieken={
                naam: float(waarde) for naam, waarde in rubrieken_decimal.items()
            },
            energieprestatie_berekening=energieprestatie_berekening.as_dict(),
            totaal_punten_bruto=float(totaal_bruto),
            correcties={
                "sanitair_extra_voorzieningen_cap_toegepast": (
                    sanitair_cap_berekening["toegepast"]
                ),
                "sanitair_extra_voorzieningen_cap": float(
                    sanitair_cap_berekening["cap"]
                ),
                "sanitair_extra_voorzieningen_punten_voor_cap": float(
                    sanitair_cap_berekening["punten_voor_cap"]
                ),
                "sanitair_extra_voorzieningen_punten_na_cap": float(
                    sanitair_cap_berekening["punten_na_cap"]
                ),
                "sanitair_extra_voorzieningen_cap_punten_badkamer": float(
                    sanitair_cap_berekening["cap_punten_badkamer"]
                ),
                "sanitair_extra_voorzieningen_cap_punten_buiten_badkamer": float(
                    sanitair_cap_berekening["cap_punten_buiten_badkamer"]
                ),
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
            "badkamer": self._badkamer_basis_punten(),
            "sanitair_extra_voorzieningen": self._sanitair_extra_voorzieningen_cap_berekening()[
                "punten_na_cap"
            ],
            "toilet": self._toilet_punten(),
            "sanitair_overig": self._sanitair_punten_buiten_badkamer_en_toiletruimte(),
            "woonvoorzieningen_handicap": self._woonvoorzieningen_handicap_punten(),
            "keuken": self._keuken_punten(),
            "vertrekken": self._vertrekken_punten(),
            "overige_ruimten": self._overige_ruimten_punten(),
            "verwarming": self._verwarming_punten(),
            "verkoeling": self._verkoeling_punten(),
            "energieprestatie": self._energieprestatie_punten(),
            "buitenruimte": self._buitenruimte_punten(),
            "parkeren": self._parkeerruimte_punten(),
            "woz": self._woz_berekening().punten,
            "bijzondere_voorzieningen": self._bijzondere_voorzieningen_punten(),
        }

    def _badkamer_punten(self):
        # Beleidsboek 2.6.1 en 2.6.2: sanitair in badkamer en extra sanitaire voorzieningen.
        return (
            self._badkamer_basis_punten()
            + self._sanitair_extra_voorzieningen_cap_berekening()["punten_na_cap"]
        )

    def _badkamer_basis_punten(self):
        # Beleidsboek 2.6.1: badkamerbasisvoorzieningen blijven in de badkamer-rubriek.
        return sum(
            (
                self._badkamer_basis_punten_per_ruimte(badkamer)
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
        # Beleidsboek 2.5.2: minder dan 1 meter = 0, tot en met 2 meter = 4,
        # en alleen langer dan 2 meter = 7 punten.
        meters = keuken.aanrechtlengte_meters or Decimal("0")
        if meters < self.kengetal.keuken_aanrecht_grens_1:
            return self.kengetal.keuken_aanrecht_punten_1
        if meters <= self.kengetal.keuken_aanrecht_grens_2:
            return self.kengetal.keuken_aanrecht_punten_2
        return self.kengetal.keuken_aanrecht_punten_3

    def _toilet_punten(self):
        # Beleidsboek 2.6.1: toilet in een toiletruimte wordt als aparte sanitaire
        # voorziening per toiletruimte gewaardeerd.
        return sum(
            (
                self._apart_toilet_punten_per_ruimte(toilet)
                for toilet in self._toilet_ruimten()
            ),
            Decimal("0"),
        )

    def _apart_toilet_punten_per_ruimte(self, toilet: ToiletRuimte) -> Decimal:
        totaal = Decimal("0")
        totaal += (
            self._waarde(toilet.toilet_staand)
            * self.kengetal.apart_toilet_staand_factor
        )
        totaal += (
            self._waarde(toilet.toilet_hangend)
            * self.kengetal.apart_toilet_hangend_factor
        )
        totaal += self._sanitair_basis_punten_per_ruimte(toilet)
        return totaal

    def _sanitair_punten_buiten_badkamer_en_toiletruimte(self) -> Decimal:
        # Beleidsboek 2.6.1: wastafel, meerpersoonswastafel, douche, bad en
        # bad/douche kunnen ook in andere vertrekken en overige ruimten voorkomen.
        return sum(
            (
                self._sanitair_basis_punten_per_ruimte(ruimte)
                for ruimte in self._sanitair_ruimten()
                if not isinstance(ruimte, (BadkamerRuimte, ToiletRuimte))
            ),
            Decimal("0"),
        )

    def _sanitair_extra_voorzieningen_cap_berekening(self) -> dict[str, Decimal | bool]:
        punten_voor_cap = sum(
            (
                self._badkamer_extra_punten_per_ruimte(badkamer)
                for badkamer in self._badkamer_ruimten()
            ),
            Decimal("0"),
        )
        cap_punten_badkamer = sum(
            (
                self._sanitair_bad_douche_basis_punten_per_ruimte(badkamer)
                for badkamer in self._badkamer_ruimten()
            ),
            Decimal("0"),
        )
        cap_punten_buiten_badkamer = sum(
            (
                self._sanitair_bad_douche_basis_punten_per_ruimte(ruimte)
                for ruimte in self._sanitair_ruimten()
                if not isinstance(ruimte, BadkamerRuimte)
            ),
            Decimal("0"),
        )
        cap = cap_punten_badkamer + cap_punten_buiten_badkamer
        # Beleidsboek 2.6.2: extra sanitaire voorzieningen worden afgetopt op het
        # totaal van douche-, bad- en bad/douchepunten.
        punten_na_cap = min(punten_voor_cap, cap)
        return {
            "toegepast": punten_na_cap != punten_voor_cap,
            "cap": cap,
            "punten_voor_cap": punten_voor_cap,
            "punten_na_cap": punten_na_cap,
            "cap_punten_badkamer": cap_punten_badkamer,
            "cap_punten_buiten_badkamer": cap_punten_buiten_badkamer,
        }

    def _woonvoorzieningen_handicap_punten(self) -> Decimal:
        if not self.gebruikersinvoer.woonvoorziening_handicap:
            return Decimal("0")

        # Beleidsboek 2.7: 1 punt per 332 euro netto-investering voor
        # woonvoorzieningen voor personen met een handicap.
        investering = self._waarde(
            self.gebruikersinvoer.woonvoorziening_handicap_netto_investering
        )
        bedrag_per_punt = Decimal(
            str(self.kengetal.woonvoorziening_handicap_bedrag_per_punt)
        )
        if bedrag_per_punt <= 0:
            return Decimal("0")
        # Beleidsboek 2.7: deze rubriek wordt naar beneden op hele punten gewaardeerd.
        return self._afronden_naar_beneden_op_hele_punten(investering / bedrag_per_punt)

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
        # Beleidsboek 2.8.1, 2.8.2 en 2.8.4: prive- en gemeenschappelijke
        # buitenruimten worden met aparte m2-systematiek gewaardeerd.
        buitenruimten = self._buitenruimten()
        if not buitenruimten:
            return Decimal("0") - self.kengetal.buitenruimte_geen_buitenruimte_aftrek

        prive_buitenruimten = [
            ruimte for ruimte in buitenruimten if isinstance(ruimte, PriveBuitenruimte)
        ]
        gemeenschappelijke_buitenruimten = [
            ruimte
            for ruimte in buitenruimten
            if isinstance(ruimte, GemeenschappelijkeBuitenruimte)
        ]

        totaal = Decimal("0")
        if prive_buitenruimten:
            prive_oppervlakte = sum(
                (ruimte.ruimte_m2 for ruimte in prive_buitenruimten),
                Decimal("0"),
            )
            totaal += self.kengetal.buitenruimte_prive_basispunten
            totaal += prive_oppervlakte * self.kengetal.buitenruimte_prive_punten_per_m2

        totaal += sum(
            (
                ruimte.ruimte_m2
                * self.kengetal.buitenruimte_gemeenschappelijke_punten_per_m2
                / Decimal(ruimte.aantal_adressen_met_toegang_en_gebruiksrecht)
                for ruimte in gemeenschappelijke_buitenruimten
            ),
            Decimal("0"),
        )

        return min(totaal, self.kengetal.buitenruimte_max_punten)

    def _buitenruimten(
        self,
    ) -> list[PriveBuitenruimte | GemeenschappelijkeBuitenruimte]:
        return [
            maak_buitenruimte(ruimte)
            for ruimte in (self.gebruikersinvoer.buitenruimten or [])
        ]

    def _energieprestatie_punten(self):
        # Beleidsboek 2.4.4 t/m 2.4.6.3: EPV gaat voor, daarna geldig label/EI,
        # en zonder geldige energieprestatie volgt waardering op bouwjaar.
        return self._energieprestatie_berekening().punten

    def _energieprestatie_berekening(self) -> EnergieprestatieBerekening:
        # Beleidsboek 2.4.4 t/m 2.4.6.3: EPV gaat voor, daarna geldig label/EI,
        # en zonder geldige energieprestatie volgt waardering op bouwjaar.
        categorie = "geen_woningtype"
        punten_voor_monumentcorrectie = Decimal("0")

        if self.gebruikersinvoer.is_eengezinswoning is None:
            return self._maak_energieprestatie_berekening(
                categorie=categorie,
                punten_voor_monumentcorrectie=punten_voor_monumentcorrectie,
            )

        if self.gebruikersinvoer.heeft_energieprestatievergoeding:
            categorie = "epv"
            punten_voor_monumentcorrectie = self._energieprestatie_epv_punten()
            return self._maak_energieprestatie_berekening(
                categorie=categorie,
                punten_voor_monumentcorrectie=punten_voor_monumentcorrectie,
            )

        if not self.gebruikersinvoer.energieprestatie_individuele_woonruimte:
            categorie = "bouwjaar_geen_individuele_woonruimte"
            punten_voor_monumentcorrectie = self._energieprestatie_bouwjaar_punten()
            return self._maak_energieprestatie_berekening(
                categorie=categorie,
                punten_voor_monumentcorrectie=punten_voor_monumentcorrectie,
            )

        label_punten = self._energieprestatie_label_punten()
        if label_punten is not None:
            return self._maak_energieprestatie_berekening(
                categorie="label",
                punten_voor_monumentcorrectie=label_punten,
            )

        energie_index_punten = self._energieprestatie_ei_punten()
        if energie_index_punten is not None:
            return self._maak_energieprestatie_berekening(
                categorie="energie_index",
                punten_voor_monumentcorrectie=energie_index_punten,
            )

        if self._genormaliseerd_energielabel():
            return self._maak_energieprestatie_berekening(
                categorie="bouwjaar_ongeldig_label",
                punten_voor_monumentcorrectie=self._energieprestatie_bouwjaar_punten(),
            )

        if self._decimaal_of_none(self.gebruikersinvoer.energie_index) is not None:
            return self._maak_energieprestatie_berekening(
                categorie="bouwjaar_ongeldige_energie_index",
                punten_voor_monumentcorrectie=self._energieprestatie_bouwjaar_punten(),
            )

        return self._maak_energieprestatie_berekening(
            categorie="bouwjaar",
            punten_voor_monumentcorrectie=self._energieprestatie_bouwjaar_punten(),
        )

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

    def _energieprestatie_epv_punten(self) -> Decimal:
        veldnaam = (
            "energieprestatie_epv_eengezinswoning_punten"
            if self.gebruikersinvoer.is_eengezinswoning
            else "energieprestatie_epv_meergezinswoning_punten"
        )
        return Decimal(str(getattr(self.kengetal, veldnaam)))

    def _energieprestatie_label_punten(self) -> Decimal | None:
        if not self._energieprestatie_heeft_geldige_registratie():
            return None

        registratiedatum = self.gebruikersinvoer.energieprestatie_registratiedatum
        label = self._genormaliseerd_energielabel()
        if not label:
            return None

        if registratiedatum < date(2015, 1, 1) or registratiedatum >= date(2021, 1, 1):
            return self._energieprestatie_labelpunten_uit_kengetal(label)
        return None

    def _energieprestatie_ei_punten(self) -> Decimal | None:
        if not self._energieprestatie_heeft_geldige_registratie():
            return None

        registratiedatum = self.gebruikersinvoer.energieprestatie_registratiedatum
        energie_index = self._decimaal_of_none(self.gebruikersinvoer.energie_index)
        if (
            energie_index is None
            or registratiedatum is None
            or registratiedatum < date(2015, 1, 1)
            or registratiedatum >= date(2021, 1, 1)
            or not self.gebruikersinvoer.energie_index_geldig_voor_wws
        ):
            return None

        band_nummer = self._energieprestatie_ei_band(energie_index)
        veldnaam = (
            f"energieprestatie_ei_punten_{band_nummer}_eengezinswoning"
            if self.gebruikersinvoer.is_eengezinswoning
            else f"energieprestatie_ei_punten_{band_nummer}_meergezinswoning"
        )
        return Decimal(str(getattr(self.kengetal, veldnaam)))

    def _energieprestatie_bouwjaar_punten(self) -> Decimal:
        bouwjaar = self._aantal_of_nul(self.gebruikersinvoer.bouwjaar)
        if bouwjaar <= 0:
            return Decimal("0")

        band_nummer = self._energieprestatie_bouwjaar_band(bouwjaar)
        veldnaam = (
            f"energieprestatie_bouwjaar_punten_{band_nummer}_eengezinswoning"
            if self.gebruikersinvoer.is_eengezinswoning
            else f"energieprestatie_bouwjaar_punten_{band_nummer}_meergezinswoning"
        )
        return Decimal(str(getattr(self.kengetal, veldnaam)))

    def _energieprestatie_monumentcorrectie(self, punten: Decimal) -> Decimal:
        if self.gebruikersinvoer.monument and punten < 0:
            # Beleidsboek 2.4.6.1: monumenten krijgen geen minpunten voor rubriek 4.
            return Decimal("0")
        return punten

    def _maak_energieprestatie_berekening(
        self, categorie: str, punten_voor_monumentcorrectie: Decimal
    ) -> EnergieprestatieBerekening:
        punten = self._energieprestatie_monumentcorrectie(punten_voor_monumentcorrectie)
        return EnergieprestatieBerekening(
            categorie=categorie,
            punten=punten,
            punten_voor_monumentcorrectie=punten_voor_monumentcorrectie,
            monumentcorrectie_toegepast=(punten != punten_voor_monumentcorrectie),
            is_eengezinswoning=self.gebruikersinvoer.is_eengezinswoning,
            individuele_woonruimte=(
                self.gebruikersinvoer.energieprestatie_individuele_woonruimte
            ),
            heeft_energieprestatievergoeding=(
                self.gebruikersinvoer.heeft_energieprestatievergoeding
            ),
            energielabel_klasse=self.gebruikersinvoer.energielabel_klasse,
            energie_index=self._decimaal_of_none(self.gebruikersinvoer.energie_index),
            energie_index_geldig_voor_wws=(
                self.gebruikersinvoer.energie_index_geldig_voor_wws
            ),
            bouwjaar=(
                None
                if self.gebruikersinvoer.bouwjaar is None
                else self._aantal_of_nul(self.gebruikersinvoer.bouwjaar)
            ),
            registratiedatum=(
                None
                if self.gebruikersinvoer.energieprestatie_registratiedatum is None
                else self.gebruikersinvoer.energieprestatie_registratiedatum.isoformat()
            ),
            peildatum=(
                None
                if self.gebruikersinvoer.energieprestatie_peildatum is None
                else self.gebruikersinvoer.energieprestatie_peildatum.isoformat()
            ),
        )

    def _energieprestatie_heeft_geldige_registratie(self) -> bool:
        registratiedatum = self.gebruikersinvoer.energieprestatie_registratiedatum
        peildatum = self.gebruikersinvoer.energieprestatie_peildatum
        if registratiedatum is None or peildatum is None:
            return False
        return registratiedatum <= peildatum

    def _energieprestatie_labelpunten_uit_kengetal(self, label: str) -> Decimal | None:
        label_sleutel = {
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
        }.get(label)
        if label_sleutel is None:
            return None

        veldnaam = (
            f"energieprestatie_label_{label_sleutel}_eengezinswoning_punten"
            if self.gebruikersinvoer.is_eengezinswoning
            else f"energieprestatie_label_{label_sleutel}_meergezinswoning_punten"
        )
        return Decimal(str(getattr(self.kengetal, veldnaam)))

    def _energieprestatie_ei_band(self, energie_index: Decimal) -> int:
        grenzen = [
            self.kengetal.energieprestatie_ei_grens_1,
            self.kengetal.energieprestatie_ei_grens_2,
            self.kengetal.energieprestatie_ei_grens_3,
            self.kengetal.energieprestatie_ei_grens_4,
            self.kengetal.energieprestatie_ei_grens_5,
            self.kengetal.energieprestatie_ei_grens_6,
            self.kengetal.energieprestatie_ei_grens_7,
            self.kengetal.energieprestatie_ei_grens_8,
        ]
        for index, grens in enumerate(grenzen, start=1):
            if energie_index <= grens:
                return index
        return 9

    def _energieprestatie_bouwjaar_band(self, bouwjaar: int) -> int:
        if bouwjaar >= self.kengetal.energieprestatie_bouwjaar_grens_1:
            return 1
        if bouwjaar >= self.kengetal.energieprestatie_bouwjaar_grens_2:
            return 2
        if bouwjaar >= self.kengetal.energieprestatie_bouwjaar_grens_3:
            return 3
        if bouwjaar >= self.kengetal.energieprestatie_bouwjaar_grens_4:
            return 4
        if bouwjaar >= self.kengetal.energieprestatie_bouwjaar_grens_5:
            return 5
        if bouwjaar >= self.kengetal.energieprestatie_bouwjaar_grens_6:
            return 6
        return 7

    def _genormaliseerd_energielabel(self) -> str:
        return (self.gebruikersinvoer.energielabel_klasse or "").strip().upper()

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
        is_zolderruimte = isinstance(ruimte, ZolderRuimte)
        heeft_vaste_trap = self._zolder_heeft_vaste_trap(ruimte)
        is_prive_parkeerruimte = naam == RuimteNaam.PRIVE_PARKEERRUIMTE

        uitsluiting_reden = None
        if effectieve_oppervlakte < Decimal("2.00"):
            # Beleidsboek 2.2.2.2 lid 2. Niet-begaanbare ruimten worden niet meer ingevoerd.
            # Beleidsboek 2.2.2.2 lid 2 en 2.2.2.4.
            uitsluiting_reden = "oppervlakte_kleiner_dan_2m2"

        punten_voor_aftrek = Decimal("0")
        aftrek_zolder_zonder_vaste_trap = Decimal("0")
        punten_na_aftrek = Decimal("0")
        if uitsluiting_reden is None:
            punten_voor_aftrek = effectieve_oppervlakte * factor
            if is_zolderruimte and not heeft_vaste_trap:
                print("Zolderruimte zonder vaste trap:", effectieve_oppervlakte, factor)
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

    def _toilet_ruimten(self) -> list[ToiletRuimte]:
        return [
            ruimte
            for ruimte in self._overige_ruimten()
            if isinstance(ruimte, ToiletRuimte)
        ]

    def _badkamer_basis_punten_per_ruimte(self, badkamer: BadkamerRuimte) -> Decimal:
        subtotal = Decimal("0")
        subtotal += (
            self._waarde(badkamer.toilet_hangend)
            * self.kengetal.badkamer_toilet_hangend_factor
        )
        subtotal += (
            self._waarde(badkamer.toilet_normaal)
            * self.kengetal.badkamer_toilet_normaal_factor
        )
        subtotal += self._sanitair_basis_punten_per_ruimte(badkamer)
        return subtotal

    def _badkamer_extra_punten_per_ruimte(self, badkamer: BadkamerRuimte) -> Decimal:
        subtotal = Decimal("0")
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

    def _sanitair_bad_douche_basis_punten(self) -> Decimal:
        return sum(
            (
                self._sanitair_bad_douche_basis_punten_per_ruimte(ruimte)
                for ruimte in self._sanitair_ruimten()
            ),
            Decimal("0"),
        )

    def _sanitair_ruimten(self) -> list[VertrekRuimte | OverigeRuimte]:
        return [*self._vertrek_ruimten(), *self._overige_ruimten()]

    def _sanitair_basis_punten_per_ruimte(
        self, ruimte: VertrekRuimte | OverigeRuimte
    ) -> Decimal:
        subtotal = self._sanitair_bad_douche_basis_punten_per_ruimte(ruimte)
        if isinstance(ruimte, BadkamerRuimte):
            subtotal += (
                self._waarde(ruimte.wastafel) * self.kengetal.badkamer_wastafel_factor
            )
            subtotal += (
                self._waarde(ruimte.meerpersoons_wastafel)
                * self.kengetal.badkamer_meerpersoons_wastafel_factor
            )
            return subtotal

        if self._aantal_of_nul(ruimte.wastafel) > 0:
            # Beleidsboek 2.6.1: wastafel in een vertrek of overige ruimte krijgt
            # maximaal 1 punt per ruimte.
            subtotal += self.kengetal.sanitair_wastafel_niet_badkamer_max_punten
        if self._aantal_of_nul(ruimte.meerpersoons_wastafel) > 0:
            # Beleidsboek 2.6.1: meerpersoonswastafel in een vertrek of overige
            # ruimte krijgt maximaal 1,5 punt per ruimte.
            subtotal += (
                self.kengetal.sanitair_meerpersoons_wastafel_niet_badkamer_max_punten
            )
        return subtotal

    def _sanitair_bad_douche_basis_punten_per_ruimte(
        self, ruimte: VertrekRuimte | OverigeRuimte
    ) -> Decimal:
        return (
            self._waarde(ruimte.douche) * self.kengetal.badkamer_douche_factor
            + self._waarde(ruimte.bad) * self.kengetal.badkamer_bad_factor
            + self._waarde(ruimte.baddouche) * self.kengetal.badkamer_baddouche_factor
        )

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
