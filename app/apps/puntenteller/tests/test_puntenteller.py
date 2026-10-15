from datetime import date
from decimal import Decimal

from apps.addresses.models import Address
from apps.puntenteller.models import Gebruikersinvoer, Kengetal, RuimteNaam
from apps.puntenteller.puntenteller import Puntenteller
from django.test import TestCase
from freezegun import freeze_time


# De minimum WOZ-waarde en de WOZ-kengetallen hangen af van de datum.
@freeze_time("2026-01-15")
class PuntentellerTest(TestCase):
    fixtures = ["fixture.json"]

    def setUp(self):
        self.adres = Address.objects.create(
            bag_id="bag-puntenteller-test",
            nummeraanduiding_id="1234567890123456",
        )

    def _maak_puntenteller(self, **overrides):
        gebruikersinvoer = Gebruikersinvoer.objects.create(
            adres=self.adres,
            **overrides,
        )
        return Puntenteller(gebruikersinvoer)

    def _bereken_resultaat(self, **overrides):
        return self._maak_puntenteller(**overrides).bereken_resultaat()

    def _bereken(self, **overrides):
        return self._maak_puntenteller(**overrides).bereken()

    def _punten(self, resultaat, naam):
        return float(resultaat.rubriek(naam).punten)

    def _omschrijvingen(self, resultaat, naam):
        return [regel.omschrijving for regel in resultaat.rubriek(naam).regels]

    def test_bereken_resultaat_geeft_punten_voor_badkamer_rubriek(self):
        resultaat = self._bereken_resultaat(
            vertrekken=[
                {
                    "naam": RuimteNaam.BADKAMER,
                    "ruimte_m2": 0,
                    "douche": 1,
                    "wastafel": 1,
                }
            ]
        )

        self.assertEqual(self._punten(resultaat, "Sanitair"), 5.0)

    def test_bereken_resultaat_geeft_punten_voor_sanitair_extra_voorzieningen_rubriek(
        self,
    ):
        resultaat = self._bereken_resultaat(
            vertrekken=[
                {
                    "naam": RuimteNaam.BADKAMER,
                    "ruimte_m2": 0,
                    "douche": 1,
                    "wastafel": 1,
                    "bubbelfunctie_bad": 1,
                    "volledige_afscheiding_douche": 1,
                    "handdoekenradiator": 1,
                    "kast_bij_wastafel": 1,
                    "kastruimte": 1,
                    "stopcontacten": 2,
                    "eenhandsmengkraan": 1,
                    "thermostatische_mengkraan": 1,
                }
            ]
        )

        # Douche 4, wastafel 1, extra voorzieningen afgetopt op 4 punten.
        self.assertEqual(self._punten(resultaat, "Sanitair"), 9.0)

    def test_bereken_resultaat_geeft_punten_voor_toilet_rubriek(self):
        resultaat = self._bereken_resultaat(
            overige_ruimten=[
                {
                    "naam": RuimteNaam.TOILETRUIMTE,
                    "ruimte_m2": 0,
                    "toilet_staand": 1,
                }
            ]
        )

        self.assertEqual(self._punten(resultaat, "Sanitair"), 3.0)

    def test_bereken_resultaat_geeft_punten_voor_douche_in_toiletruimte(self):
        # Beleidsboek 2.6.1: een douche telt mee in elke ruimte.
        resultaat = self._bereken_resultaat(
            overige_ruimten=[
                {
                    "naam": RuimteNaam.TOILETRUIMTE,
                    "ruimte_m2": 0,
                    "toilet_staand": 1,
                    "douche": 1,
                }
            ]
        )

        self.assertEqual(self._punten(resultaat, "Sanitair"), 7.0)

    def test_bereken_resultaat_geeft_punten_voor_sanitair_overig_rubriek(self):
        resultaat = self._bereken_resultaat(
            overige_ruimten=[
                {
                    "naam": RuimteNaam.BERGING,
                    "ruimte_m2": 0,
                    "wastafel": 1,
                }
            ]
        )

        self.assertEqual(self._punten(resultaat, "Sanitair"), 1.0)

    def test_bereken_resultaat_geeft_punten_voor_woonvoorzieningen_handicap_rubriek(
        self,
    ):
        resultaat = self._bereken_resultaat(
            woonvoorziening_handicap=True,
            woonvoorziening_handicap_netto_investering=700,
        )

        self.assertEqual(
            self._punten(resultaat, "Woonvoorzieningen voor personen met een handicap"),
            2.0,
        )

    def test_bereken_resultaat_geeft_punten_voor_keuken_rubriek(self):
        resultaat = self._bereken_resultaat(
            vertrekken=[
                {
                    "naam": RuimteNaam.KEUKEN,
                    "ruimte_m2": 0,
                    "aanrechtlengte_meters": 2,
                    "inbouw_koelkast": 1,
                    "extra_kastruimte": 1,
                }
            ]
        )

        self.assertEqual(self._punten(resultaat, "Keuken"), 5.75)

    def test_bereken_resultaat_begrenst_extra_keukenpunten_op_aanrechtpunten(self):
        resultaat = self._bereken_resultaat(
            vertrekken=[
                {
                    "naam": RuimteNaam.KEUKEN,
                    "ruimte_m2": 0,
                    "aanrechtlengte_meters": 2,
                    "inbouw_afzuiginstallatie": 1,
                    "inbouw_kookplaat_inductie": 1,
                    "inbouw_koelkast": 1,
                    "inbouw_vaatwasmachine": 1,
                }
            ]
        )

        self.assertEqual(self._punten(resultaat, "Keuken"), 8.0)

    def test_bereken_resultaat_geeft_punten_voor_vertrekken_rubriek(self):
        resultaat = self._bereken_resultaat(
            vertrekken=[
                {
                    "naam": RuimteNaam.WOONKAMER,
                    "ruimte_m2": 10,
                    "aantal_adressen_met_toegang_en_gebruiksrecht": 1,
                }
            ]
        )

        self.assertEqual(self._punten(resultaat, "Oppervlakte vertrekken"), 10.0)

    def test_bereken_resultaat_deelt_vertrekpunten_over_aantal_adressen(self):
        resultaat = self._bereken_resultaat(
            vertrekken=[
                {
                    "naam": RuimteNaam.WOONKAMER,
                    "ruimte_m2": 10,
                    "aantal_adressen_met_toegang_en_gebruiksrecht": 2,
                }
            ]
        )

        self.assertEqual(self._punten(resultaat, "Gemeenschappelijke ruimten"), 5.0)

    def test_bereken_resultaat_geeft_punten_voor_overige_ruimten_rubriek(self):
        resultaat = self._bereken_resultaat(
            overige_ruimten=[
                {
                    "naam": RuimteNaam.BERGING,
                    "ruimte_m2": 4,
                }
            ]
        )

        self.assertEqual(self._punten(resultaat, "Oppervlakte overige ruimten"), 3.0)

    def test_bereken_resultaat_geeft_punten_voor_verwarming_rubriek(self):
        resultaat = self._bereken_resultaat(
            vertrekken=[
                {
                    "naam": RuimteNaam.WOONKAMER,
                    "ruimte_m2": 0,
                    "verwarmd": True,
                }
            ],
            overige_ruimten=[
                {
                    "naam": RuimteNaam.BERGING,
                    "ruimte_m2": 0,
                    "verwarmd": True,
                }
            ],
            verkeersruimten=[
                {
                    "naam": RuimteNaam.VERKEERSRUIMTE,
                    "ruimte_m2": 0,
                    "verwarmd": True,
                }
            ],
        )

        self.assertEqual(self._punten(resultaat, "Verwarming en verkoeling"), 4.0)

    def test_bereken_resultaat_geeft_punten_voor_verkoeling_rubriek(self):
        resultaat = self._bereken_resultaat(
            vertrekken=[
                {
                    "naam": RuimteNaam.WOONKAMER,
                    "ruimte_m2": 0,
                    "verwarmd": True,
                    "gekoeld": True,
                }
            ]
        )

        # Verwarmd vertrek 2 punten, verkoeling 1 punt.
        self.assertEqual(self._punten(resultaat, "Verwarming en verkoeling"), 3.0)

    def test_bereken_resultaat_geeft_punten_voor_energieprestatie_rubriek(self):
        resultaat = self._bereken_resultaat(
            is_eengezinswoning=True,
            energielabel_klasse="A",
        )

        self.assertEqual(self._punten(resultaat, "Energieprestatie"), 41.0)

    def test_bereken_resultaat_geeft_punten_voor_energieprestatie_index(self):
        resultaat = self._bereken_resultaat(
            is_eengezinswoning=True, energie_index="0.60"
        )

        self.assertEqual(self._punten(resultaat, "Energieprestatie"), 52.0)

    def test_bereken_resultaat_geeft_punten_voor_energieprestatie_bouwjaar(self):
        resultaat = self._bereken_resultaat(is_eengezinswoning=True, bouwjaar=1995)

        self.assertEqual(self._punten(resultaat, "Energieprestatie"), 22.0)

    def test_bereken_resultaat_geeft_punten_voor_buitenruimte_rubriek(self):
        resultaat = self._bereken_resultaat(
            buitenruimten=[
                {
                    "naam": RuimteNaam.PRIVE_BUITENRUIMTE,
                    "ruimte_m2": 10,
                }
            ]
        )

        self.assertEqual(self._punten(resultaat, "Buitenruimten"), 5.5)

    def test_bereken_resultaat_deelt_gemeenschappelijke_buitenruimte_over_aantal_adressen(
        self,
    ):
        resultaat = self._bereken_resultaat(
            buitenruimten=[
                {
                    "naam": RuimteNaam.GEMEENSCHAPPELIJKE_BUITENRUIMTE,
                    "ruimte_m2": 10,
                    "aantal_adressen_met_toegang_en_gebruiksrecht": 2,
                }
            ]
        )

        self.assertEqual(self._punten(resultaat, "Buitenruimten"), 3.75)

    def test_bereken_resultaat_trekt_vijf_punten_af_zonder_buitenruimte(self):
        resultaat = self._bereken_resultaat()

        self.assertEqual(self._punten(resultaat, "Buitenruimten"), -5.0)

    def test_bereken_resultaat_geeft_punten_voor_parkeren_rubriek(self):
        resultaat = self._bereken_resultaat(
            parkeerruimten=[
                {
                    "naam": RuimteNaam.BUITENRUIMTE_PARKEERPLAATS,
                    "type": "gesloten_garage_bij_complex",
                }
            ]
        )

        self.assertEqual(self._punten(resultaat, "Parkeren"), 9.0)

    def test_bereken_resultaat_deelt_parkeerpunten_over_aantal_adressen(self):
        resultaat = self._bereken_resultaat(
            parkeerruimten=[
                {
                    "naam": RuimteNaam.BUITENRUIMTE_PARKEERPLAATS,
                    "type": "gesloten_garage_bij_complex",
                    "aantal_adressen_met_toegang_en_gebruiksrecht": 2,
                }
            ]
        )

        self.assertEqual(self._punten(resultaat, "Parkeren"), 4.5)

    def test_bereken_resultaat_geeft_punten_voor_woz_rubriek(self):
        resultaat = self._bereken_resultaat(
            vertrekken=[
                {
                    "naam": RuimteNaam.WOONKAMER,
                    "ruimte_m2": 100,
                }
            ],
            woz_waarde=200000,
            woz_peildatum_jaar=2025,
        )

        self.assertEqual(self._punten(resultaat, "WOZ-waarde"), 19.25)

    def test_bereken_resultaat_past_woz_cap_toe_boven_maximum(self):
        resultaat = self._bereken_resultaat(
            vertrekken=[{"naam": RuimteNaam.WOONKAMER, "ruimte_m2": 200}],
            buitenruimten=[{"naam": RuimteNaam.PRIVE_BUITENRUIMTE, "ruimte_m2": 10}],
            woz_waarde=2000000,
            woz_peildatum_jaar=2025,
        )

        self.assertIn(
            "Afgetopt op 33% van het totaal",
            self._omschrijvingen(resultaat, "WOZ-waarde"),
        )
        self.assertEqual(self._punten(resultaat, "WOZ-waarde"), 101.0)
        self.assertEqual(resultaat.totaal_punten, 307)

    def test_bereken_resultaat_waardeert_woz_cap_minimaal_op_186_punten(self):
        resultaat = self._bereken_resultaat(
            vertrekken=[{"naam": RuimteNaam.WOONKAMER, "ruimte_m2": 92}],
            buitenruimten=[{"naam": RuimteNaam.PRIVE_BUITENRUIMTE, "ruimte_m2": 10}],
            woz_waarde=1200000,
            woz_peildatum_jaar=2025,
        )

        self.assertEqual(
            self._omschrijvingen(resultaat, "WOZ-waarde")[-2:],
            ["Afgetopt op 33% van het totaal", "Minimale waardering 186 punten"],
        )
        self.assertEqual(resultaat.totaal_punten, 186)

    def test_bereken_resultaat_sluit_woz_cap_uit_onder_187_punten(self):
        resultaat = self._bereken_resultaat(
            vertrekken=[{"naam": RuimteNaam.WOONKAMER, "ruimte_m2": 90}],
            buitenruimten=[{"naam": RuimteNaam.PRIVE_BUITENRUIMTE, "ruimte_m2": 10}],
            woz_waarde=900000,
            woz_peildatum_jaar=2025,
        )

        self.assertNotIn(
            "Afgetopt op 33% van het totaal",
            self._omschrijvingen(resultaat, "WOZ-waarde"),
        )

    def test_bereken_resultaat_past_geen_minimale_waardering_toe_bij_kleine_nieuwbouwwoning(
        self,
    ):
        resultaat = self._bereken_resultaat(
            vertrekken=[{"naam": RuimteNaam.WOONKAMER, "ruimte_m2": 92}],
            buitenruimten=[{"naam": RuimteNaam.PRIVE_BUITENRUIMTE, "ruimte_m2": 10}],
            woz_waarde=1200000,
            woz_peildatum_jaar=2025,
            woz_kleine_nieuwbouwwoning=True,
        )

        self.assertEqual(
            self._omschrijvingen(resultaat, "WOZ-waarde")[-1],
            "Afgetopt op 33% van het totaal",
        )
        self.assertEqual(self._punten(resultaat, "WOZ-waarde"), 48.0)
        self.assertEqual(resultaat.totaal_punten, 146)

    def test_bereken_resultaat_verhoogt_zorgwoning_totaal_met_35_procent(self):
        resultaat = self._bereken_resultaat(
            zorgwoning=True,
            vertrekken=[{"naam": RuimteNaam.WOONKAMER, "ruimte_m2": 20}],
            buitenruimten=[{"naam": RuimteNaam.PRIVE_BUITENRUIMTE, "ruimte_m2": 20}],
        )

        # Basis 50 (vertrek 20, buiten 9, WOZ 21): 50 x 35% = 17,5.
        self.assertEqual(self._punten(resultaat, "Zorgwoning"), 17.5)
        self.assertEqual(resultaat.totaal_punten, 68)

    def test_bereken_resultaat_geeft_rijksmonument_extra_punten_voor_oude_huurovereenkomst(
        self,
    ):
        resultaat = self._bereken_resultaat(
            monument=True,
            monument_soort="rijksmonument",
            huurovereenkomst_afgesloten_op=date(2024, 6, 30),
            vertrekken=[{"naam": RuimteNaam.WOONKAMER, "ruimte_m2": 100}],
            buitenruimten=[{"naam": RuimteNaam.PRIVE_BUITENRUIMTE, "ruimte_m2": 10}],
        )

        self.assertEqual(self._punten(resultaat, "Rijksmonument"), 50.0)
        self.assertEqual(resultaat.totaal_punten, 164)

    def test_bereken_resultaat_geeft_rijksmonument_huurprijsopslag_vanaf_wet_betaalbare_huur(
        self,
    ):
        resultaat = self._bereken_resultaat(
            monument=True,
            monument_soort="rijksmonument",
            huurovereenkomst_afgesloten_op=date(2024, 7, 1),
            vertrekken=[{"naam": RuimteNaam.WOONKAMER, "ruimte_m2": 100}],
            buitenruimten=[{"naam": RuimteNaam.PRIVE_BUITENRUIMTE, "ruimte_m2": 10}],
        )

        # Beleidsboek 2.13.3: 35% op de maximale huurprijs, niet op de punten.
        self.assertEqual(resultaat.totaal_punten, 114)
        self.assertEqual(
            resultaat.as_dict()["huurprijsopslagen"],
            [{"naam": "Rijksmonument", "procent": 35.0}],
        )

    def test_bereken_resultaat_geeft_punten_voor_bijzondere_voorzieningen_rubriek(
        self,
    ):
        resultaat = self._bereken_resultaat(
            bijzondere_voorziening_intercom_met_beeld=True,
            bijzondere_voorziening_laadpalen=1,
        )

        # Beleidsboek 2.12.2 en 2.12.3: aanbelfunctie 0,25 en laadpaal 2 punten.
        self.assertEqual(self._punten(resultaat, "Bijzondere voorzieningen"), 2.25)

    def test_bereken_resultaat_geeft_punten_voor_parkeren_in_telformaat(self):
        # Dit is het formaat dat de ParkeerruimteSerializer opslaat.
        resultaat = self._bereken_resultaat(
            parkeerruimten=[
                {
                    "naam": RuimteNaam.BUITENRUIMTE_PARKEERPLAATS,
                    "aantal_gesloten_garage_bij_complex": 1,
                    "aantal_buiten_bij_complex_zonder_dak": 1,
                    "aantal_laadpalen": 1,
                    "aantal_adressen_met_toegang_en_gebruiksrecht": 1,
                }
            ]
        )

        self.assertEqual(self._punten(resultaat, "Parkeren"), 15.0)

    def test_bereken_resultaat_geeft_zeven_punten_voor_aanrecht_langer_dan_twee_meter(
        self,
    ):
        resultaat = self._bereken_resultaat(
            vertrekken=[
                {
                    "naam": RuimteNaam.KEUKEN,
                    "ruimte_m2": 0,
                    "aanrechtlengte_meters": 3,
                }
            ]
        )

        self.assertEqual(self._punten(resultaat, "Keuken"), 7.0)

    def test_bereken_resultaat_geeft_geen_keukenpunten_voor_aanrecht_korter_dan_een_meter(
        self,
    ):
        resultaat = self._bereken_resultaat(
            vertrekken=[
                {
                    "naam": RuimteNaam.KEUKEN,
                    "ruimte_m2": 0,
                    "aanrechtlengte_meters": "0.5",
                    "inbouw_koelkast": 1,
                }
            ]
        )

        self.assertEqual(self._punten(resultaat, "Keuken"), 0.0)

    def test_bereken_resultaat_geeft_punten_voor_meerpersoonswastafel_buiten_badkamer(
        self,
    ):
        resultaat = self._bereken_resultaat(
            overige_ruimten=[
                {
                    "naam": RuimteNaam.BERGING,
                    "ruimte_m2": 0,
                    "meerpersoons_wastafel": 2,
                }
            ]
        )

        self.assertEqual(self._punten(resultaat, "Sanitair"), 1.5)

    def test_bereken_resultaat_begrenst_verwarming_van_overige_ruimten_op_vier(self):
        resultaat = self._bereken_resultaat(
            overige_ruimten=[
                {"naam": RuimteNaam.BERGING, "ruimte_m2": 0, "verwarmd": True}
            ]
            * 5
        )

        self.assertEqual(self._punten(resultaat, "Verwarming en verkoeling"), 4.0)

    def test_bereken_resultaat_begrenst_verkoeling_op_twee_punten(self):
        resultaat = self._bereken_resultaat(
            vertrekken=[
                {
                    "naam": RuimteNaam.WOONKAMER,
                    "ruimte_m2": 0,
                    "verwarmd": True,
                    "gekoeld": True,
                }
            ]
            * 3
        )

        # 3 verwarmde vertrekken 6 punten, verkoeling begrensd op 2 punten.
        self.assertEqual(self._punten(resultaat, "Verwarming en verkoeling"), 8.0)

    def test_bereken_resultaat_begrenst_buitenruimte_op_maximum(self):
        resultaat = self._bereken_resultaat(
            buitenruimten=[{"naam": RuimteNaam.PRIVE_BUITENRUIMTE, "ruimte_m2": 100}]
        )

        self.assertEqual(self._punten(resultaat, "Buitenruimten"), 15.0)

    def test_bereken_resultaat_trekt_punten_af_voor_zolder_zonder_vaste_trap(self):
        resultaat = self._bereken_resultaat(
            overige_ruimten=[
                {
                    "naam": RuimteNaam.ZOLDER,
                    "ruimte_m2": 10,
                    "heeft_vaste_trap": False,
                    "aftrek_loopruimte_m2": 2,
                }
            ]
        )

        self.assertEqual(self._punten(resultaat, "Oppervlakte overige ruimten"), 1.0)

    def test_bereken_resultaat_geeft_punten_voor_energieprestatievergoeding(self):
        resultaat = self._bereken_resultaat(
            is_eengezinswoning=True,
            heeft_energieprestatievergoeding=True,
            energielabel_klasse="A",
        )

        self.assertEqual(self._punten(resultaat, "Energieprestatie"), 32.0)
        self.assertEqual(
            self._omschrijvingen(resultaat, "Energieprestatie"),
            ["Energieprestatievergoeding, eengezinswoning"],
        )

    def test_bereken_resultaat_geeft_minpunten_voor_oud_bouwjaar(self):
        resultaat = self._bereken_resultaat(is_eengezinswoning=True, bouwjaar=1970)

        self.assertEqual(self._punten(resultaat, "Energieprestatie"), -15.0)

    def test_bereken_resultaat_geeft_monument_geen_minpunten_voor_energieprestatie(
        self,
    ):
        resultaat = self._bereken_resultaat(
            is_eengezinswoning=True,
            energielabel_klasse="G",
            monument=True,
            monument_soort="rijksmonument",
        )

        self.assertEqual(self._punten(resultaat, "Energieprestatie"), 0.0)

    def test_bereken_resultaat_geeft_woz_geen_punten_bij_onbekend_peiljaar(self):
        resultaat = self._bereken_resultaat(
            vertrekken=[{"naam": RuimteNaam.WOONKAMER, "ruimte_m2": 100}],
            woz_waarde=200000,
            woz_peildatum_jaar=2019,
        )

        self.assertEqual(self._punten(resultaat, "WOZ-waarde"), 0.0)

    def test_bereken_resultaat_corrigeert_woz_voor_bouwvoltooiingspercentage(self):
        resultaat = self._bereken_resultaat(
            vertrekken=[{"naam": RuimteNaam.WOONKAMER, "ruimte_m2": 100}],
            woz_waarde=100000,
            woz_peildatum_jaar=2025,
            woz_bouwvoltooiingspercentage=50,
        )

        self.assertEqual(self._punten(resultaat, "WOZ-waarde"), 19.25)

    def test_bereken_resultaat_geeft_minimaal_40_woz_punten_bij_nieuwbouw_2015_2019(
        self,
    ):
        # Beleidsboek 2.11.5: 120 m² min 5 punten zonder buitenruimte is 115 punten
        # in de overige rubrieken, dus minimaal 40 WOZ-punten.
        resultaat = self._bereken_resultaat(
            vertrekken=[{"naam": RuimteNaam.WOONKAMER, "ruimte_m2": 120}],
            woz_waarde=200000,
            woz_peildatum_jaar=2025,
            woz_nieuwbouw_2015_2019=True,
        )

        self.assertEqual(self._punten(resultaat, "WOZ-waarde"), 18.0)
        self.assertEqual(
            self._punten(resultaat, "WOZ-waarde nieuwbouw 2015-2019"), 22.0
        )

    def test_bereken_resultaat_geeft_geen_woz_minimum_onder_110_punten(self):
        resultaat = self._bereken_resultaat(
            vertrekken=[{"naam": RuimteNaam.WOONKAMER, "ruimte_m2": 100}],
            woz_waarde=200000,
            woz_peildatum_jaar=2025,
            woz_nieuwbouw_2015_2019=True,
        )

        self.assertEqual(self._punten(resultaat, "WOZ-waarde"), 19.25)
        self.assertNotIn(
            "WOZ-waarde nieuwbouw 2015-2019",
            [r.naam for r in resultaat.rubrieken],
        )

    def test_bereken_resultaat_geeft_gemeentelijk_monument_huurprijsopslag(self):
        resultaat = self._bereken_resultaat(
            monument=True,
            monument_soort="gemeentelijk_monument",
            vertrekken=[{"naam": RuimteNaam.WOONKAMER, "ruimte_m2": 100}],
            buitenruimten=[{"naam": RuimteNaam.PRIVE_BUITENRUIMTE, "ruimte_m2": 10}],
        )

        self.assertEqual(resultaat.totaal_punten, 114)
        self.assertEqual(
            resultaat.as_dict()["huurprijsopslagen"],
            [{"naam": "Gemeentelijk monument", "procent": 15.0}],
        )

    def test_bereken_resultaat_telt_huurprijsopslagen_op(self):
        # Beleidsboek 2.13.1 en 2.13.5: beschermd gezicht 5% plus nieuwbouw 10%.
        # Nieuwbouw alleen in de middensector (144 t/m 186 punten).
        resultaat = self._bereken_resultaat(
            monument=True,
            monument_soort="beschermd_stads_of_dorpsgezicht",
            bouwjaar=1930,
            nieuwbouw=True,
            vertrekken=[{"naam": RuimteNaam.WOONKAMER, "ruimte_m2": 140}],
            buitenruimten=[{"naam": RuimteNaam.PRIVE_BUITENRUIMTE, "ruimte_m2": 10}],
        ).as_dict()

        self.assertEqual(resultaat["huurprijsopslag_procent"], 15.0)

    def test_bereken_resultaat_geeft_geen_nieuwbouwopslag_buiten_middensector(self):
        resultaat = self._bereken_resultaat(
            nieuwbouw=True,
            vertrekken=[{"naam": RuimteNaam.WOONKAMER, "ruimte_m2": 100}],
        ).as_dict()

        self.assertLess(resultaat["totaal_punten"], 144)
        self.assertEqual(resultaat["huurprijsopslagen"], [])

    def test_bereken_resultaat_totaal_is_som_van_rubrieken_en_opslagen(self):
        resultaat = self._bereken_resultaat(
            zorgwoning=True,
            nieuwbouw=True,
            vertrekken=[
                {"naam": RuimteNaam.WOONKAMER, "ruimte_m2": 25},
                {"naam": RuimteNaam.KEUKEN, "ruimte_m2": 8, "aanrechtlengte_meters": 3},
            ],
            woz_waarde=300000,
            woz_peildatum_jaar=2025,
        ).as_dict()

        for rubriek in [*resultaat["rubrieken"], *resultaat["opslagen"]]:
            self.assertAlmostEqual(
                rubriek["punten"], sum(r["punten"] for r in rubriek["regels"])
            )
        self.assertAlmostEqual(
            resultaat["totaal_punten"],
            sum(r["punten"] for r in [*resultaat["rubrieken"], *resultaat["opslagen"]]),
        )
        self.assertEqual(
            [opslag["naam"] for opslag in resultaat["opslagen"]],
            ["Zorgwoning", "Afronding"],
        )

    def test_bereken_resultaat_toont_deling_over_adressen_als_aparte_regel(self):
        resultaat = self._bereken_resultaat(
            vertrekken=[
                {
                    "naam": RuimteNaam.WOONKAMER,
                    "ruimte_m2": 10,
                    "aantal_adressen_met_toegang_en_gebruiksrecht": 2,
                }
            ]
        )

        self.assertEqual(
            [
                r.as_dict()
                for r in resultaat.rubriek("Gemeenschappelijke ruimten").regels
            ],
            [
                {
                    "omschrijving": "Oppervlakte in m²",
                    "punten": 10.0,
                    "ruimte": "Woonkamer",
                    "aantal": 10.0,
                    "factor": 1.0,
                },
                {
                    "omschrijving": "Gedeeld door 2 adressen",
                    "punten": -5.0,
                    "ruimte": "Woonkamer",
                    "aantal": None,
                    "factor": None,
                },
            ],
        )

    def test_bereken_resultaat_toont_geen_ruimte_bij_keuken_en_parkeren(self):
        # De rubriek heet al naar de ruimte, dus "Keuken: ..." is dubbelop.
        resultaat = self._bereken_resultaat(
            vertrekken=[
                {
                    "naam": RuimteNaam.KEUKEN,
                    "ruimte_m2": 0,
                    "aanrechtlengte_meters": 3,
                    "inbouw_koelkast": 1,
                }
            ],
            parkeerruimten=[
                {
                    "naam": RuimteNaam.BUITENRUIMTE_PARKEERPLAATS,
                    "aantal_gesloten_garage_bij_complex": 1,
                    "aantal_laadpalen": 1,
                }
            ],
        )

        for naam in ["Keuken", "Parkeren"]:
            regels = resultaat.rubriek(naam).regels
            self.assertTrue(regels)
            self.assertEqual(
                [r.as_dict()["ruimte"] for r in regels], [None] * len(regels)
            )

    def test_bereken_resultaat_rondt_rubriek_af_op_kwartpunt(self):
        # Beleidsboek 2.1.4 en 2.9.7: 10 m2 gedeeld door 3 adressen is 3,33 en
        # wordt 3,25.
        resultaat = self._bereken_resultaat(
            vertrekken=[
                {
                    "naam": RuimteNaam.WOONKAMER,
                    "ruimte_m2": 10,
                    "aantal_adressen_met_toegang_en_gebruiksrecht": 3,
                }
            ]
        )

        rubriek = next(
            r
            for r in resultaat.as_dict()["rubrieken"]
            if r["naam"] == "Gemeenschappelijke ruimten"
        )
        self.assertEqual(rubriek["punten"], 3.25)
        self.assertEqual(
            [(r["omschrijving"], r["punten"]) for r in rubriek["regels"]],
            [
                ("Oppervlakte in m²", 10.0),
                ("Gedeeld door 3 adressen", -6.67),
                ("Afronding op kwartpunt", -0.08),
            ],
        )

    def test_bereken_resultaat_toont_woz_onderdelen_op_twee_decimalen(self):
        # Beleidsboek 2.11.2: onderdeel I en II worden niet afgerond, de som
        # wel. In de weergave tellen de afgeronde regels op tot de rubriek.
        resultaat = self._bereken_resultaat(
            vertrekken=[{"naam": RuimteNaam.WOONKAMER, "ruimte_m2": 60}],
            woz_waarde=300000,
            woz_peildatum_jaar=2025,
        )

        rubriek = next(
            r for r in resultaat.as_dict()["rubrieken"] if r["naam"] == "WOZ-waarde"
        )
        self.assertEqual(rubriek["punten"], 36.25)
        self.assertEqual([r["punten"] for r in rubriek["regels"]], [17.69, 18.66, -0.1])

    def test_bereken_resultaat_zorgwoningtoeslag_zonder_bijzondere_voorzieningen(self):
        # Beleidsboek 2.1.5: de toeslag gaat over rubriek 1 t/m 11.1, dus niet
        # over de laadpalen in rubriek 12. 50 x 35% = 17,5.
        resultaat = self._bereken_resultaat(
            zorgwoning=True,
            bijzondere_voorziening_laadpalen=2,
            vertrekken=[{"naam": RuimteNaam.WOONKAMER, "ruimte_m2": 20}],
            buitenruimten=[{"naam": RuimteNaam.PRIVE_BUITENRUIMTE, "ruimte_m2": 20}],
        )

        self.assertEqual(self._punten(resultaat, "Zorgwoning"), 17.5)

    def test_bereken_resultaat_geeft_minpunten_energie_bij_beschermd_gezicht(self):
        # Beleidsboek 2.4.6.1 geldt alleen voor rijks-, provinciale en
        # gemeentelijke monumenten.
        resultaat = self._bereken_resultaat(
            is_eengezinswoning=True,
            energielabel_klasse="G",
            monument=True,
            monument_soort="beschermd_stads_of_dorpsgezicht",
        )

        self.assertEqual(self._punten(resultaat, "Energieprestatie"), -15.0)

    def test_bereken_resultaat_rondt_vertrekken_af_op_hele_m2(self):
        # Beleidsboek 2.2.1.1: 10,3 + 12,3 = 22,6 m², afgerond 23 m².
        resultaat = self._bereken_resultaat(
            vertrekken=[
                {"naam": RuimteNaam.WOONKAMER, "ruimte_m2": "10.30"},
                {"naam": RuimteNaam.SLAAPKAMER, "ruimte_m2": "12.30"},
            ]
        )

        self.assertEqual(self._punten(resultaat, "Oppervlakte vertrekken"), 23.0)
        self.assertEqual(
            self._omschrijvingen(resultaat, "Oppervlakte vertrekken")[-1],
            "Afronding op hele m² (22,6 m² wordt 23 m²)",
        )

    def test_bereken_resultaat_rondt_woonvoorzieningen_handicap_af_op_hele_punten(
        self,
    ):
        # Beleidsboek 2.7, net als de Huurcommissie: 800 / 332 = 2,41, wordt 2.
        resultaat = self._bereken_resultaat(
            woonvoorziening_handicap=True,
            woonvoorziening_handicap_netto_investering=800,
        )

        self.assertEqual(
            self._punten(resultaat, "Woonvoorzieningen voor personen met een handicap"),
            2.0,
        )

    def test_bereken_resultaat_begrenst_stopcontacten_per_wastafel(self):
        # Beleidsboek 2.6.2: maximaal twee stopcontacten per wastafel.
        resultaat = self._bereken_resultaat(
            vertrekken=[
                {
                    "naam": RuimteNaam.BADKAMER,
                    "ruimte_m2": 0,
                    "douche": 1,
                    "wastafel": 2,
                    "stopcontacten": 5,
                }
            ]
        )

        # Douche 4, twee wastafels 2, vier stopcontacten 1.
        self.assertEqual(self._punten(resultaat, "Sanitair"), 7.0)

    def test_bereken_resultaat_deelt_verwarming_van_gedeelde_ruimte(self):
        # Beleidsboek 2.9.2: ook verwarming wordt gedeeld door het aantal adressen.
        resultaat = self._bereken_resultaat(
            vertrekken=[
                {
                    "naam": RuimteNaam.WOONKAMER,
                    "ruimte_m2": 0,
                    "verwarmd": True,
                    "aantal_adressen_met_toegang_en_gebruiksrecht": 2,
                }
            ]
        )

        self.assertEqual(self._punten(resultaat, "Gemeenschappelijke ruimten"), 1.0)

    def test_bereken_resultaat_gebruikt_minimum_woz_waarde_zonder_woz_waarde(self):
        # Beleidsboek 2.11.1: per 1 januari 2026 is de minimum WOZ-waarde € 85.806.
        resultaat = self._bereken_resultaat(
            vertrekken=[{"naam": RuimteNaam.WOONKAMER, "ruimte_m2": 20}]
        )

        self.assertEqual(
            self._omschrijvingen(resultaat, "WOZ-waarde")[0],
            "Onderdeel I: minimum WOZ-waarde € 85.806 / 16.954",
        )
        self.assertEqual(self._punten(resultaat, "WOZ-waarde"), 21.0)

    def test_bereken_resultaat_waardeert_gemeenschappelijke_ruimten_zorgwoning_vast(
        self,
    ):
        # Beleidsboek 2.9.4: bij een zorgwoning 3 punten in plaats van meten.
        resultaat = self._bereken_resultaat(
            zorgwoning=True,
            vertrekken=[
                {
                    "naam": RuimteNaam.WOONKAMER,
                    "ruimte_m2": 60,
                    "aantal_adressen_met_toegang_en_gebruiksrecht": 10,
                }
            ],
        )

        self.assertEqual(self._punten(resultaat, "Gemeenschappelijke ruimten"), 3.0)

    def test_bereken_resultaat_geeft_geen_extra_sanitair_zonder_wastafel(self):
        # Beleidsboek 2.6.2: extra voorzieningen alleen in een ruimte met wastafel.
        resultaat = self._bereken_resultaat(
            vertrekken=[
                {
                    "naam": RuimteNaam.BADKAMER,
                    "ruimte_m2": 0,
                    "douche": 1,
                    "handdoekenradiator": 1,
                }
            ]
        )

        self.assertEqual(self._punten(resultaat, "Sanitair"), 4.0)

    def test_bereken_resultaat_waardeert_klein_vertrek_als_overige_ruimte(self):
        # Beleidsboek 2.2.1.2 en 2.2.2.2: een vertrek kleiner dan 4 m² is een
        # overige ruimte. 3 m² x 0,75 = 2,25.
        resultaat = self._bereken_resultaat(
            vertrekken=[{"naam": RuimteNaam.SLAAPKAMER, "ruimte_m2": 3}]
        )

        self.assertEqual(self._punten(resultaat, "Oppervlakte vertrekken"), 0.0)
        self.assertEqual(self._punten(resultaat, "Oppervlakte overige ruimten"), 2.25)

    def test_bereken_resultaat_geeft_geen_opslag_beschermd_gezicht_vanaf_1965(self):
        # Beleidsboek 2.13.5: alleen voor woningen gebouwd vóór 1965.
        resultaat = self._bereken_resultaat(
            monument=True,
            monument_soort="beschermd_stads_of_dorpsgezicht",
            bouwjaar=1965,
        ).as_dict()

        self.assertEqual(resultaat["huurprijsopslagen"], [])

    def test_bereken_resultaat_rondt_zorgwoningtoeslag_af_op_kwartpunt(self):
        # Net als de Huurcommissie: basis 50,25 x 35% = 17,5875, wordt 17,5.
        resultaat = self._bereken_resultaat(
            zorgwoning=True,
            vertrekken=[{"naam": RuimteNaam.WOONKAMER, "ruimte_m2": 21}],
            buitenruimten=[{"naam": RuimteNaam.PRIVE_BUITENRUIMTE, "ruimte_m2": 20}],
        )

        self.assertEqual(self._punten(resultaat, "Zorgwoning"), 17.5)
        self.assertEqual(resultaat.totaal_punten, 68)

    def test_bereken_resultaat_geeft_zorgwoning_zonder_gedeelde_ruimten_geen_3_punten(
        self,
    ):
        # Beleidsboek 2.9.4: de vaste 3 punten vervangen het meten van gedeelde
        # ruimten. Zonder gedeelde ruimten geen punten.
        resultaat = self._bereken_resultaat(
            zorgwoning=True,
            vertrekken=[{"naam": RuimteNaam.WOONKAMER, "ruimte_m2": 20}],
        )

        self.assertEqual(self._punten(resultaat, "Gemeenschappelijke ruimten"), 0.0)

    def test_bereken_resultaat_deelt_gedeelde_garages_in_woz_en_parkeren(self):
        # Beleidsboek 2.10.3 en 2.11.4, vergeleken met de Huurcommissie: 20 garages
        # voor 20 adressen geven 9 punten en 20 x 12 / 20 = 12 m² voor WOZ.
        resultaat = self._bereken_resultaat(
            vertrekken=[{"naam": RuimteNaam.WOONKAMER, "ruimte_m2": 61}],
            woz_waarde=316000,
            woz_peildatum_jaar=2025,
            parkeerruimten=[
                {
                    "naam": RuimteNaam.BUITENRUIMTE_PARKEERPLAATS,
                    "aantal_gesloten_garage_bij_complex": 20,
                    "aantal_adressen_met_toegang_en_gebruiksrecht": 20,
                }
            ],
        )

        self.assertEqual(
            self._omschrijvingen(resultaat, "Parkeren"),
            ["Gesloten garage bij complex", "Gedeeld door 20 adressen"],
        )
        self.assertEqual(self._punten(resultaat, "Parkeren"), 9.0)
        self.assertIn("(73 m² × 268)", self._omschrijvingen(resultaat, "WOZ-waarde")[1])
        self.assertEqual(self._punten(resultaat, "WOZ-waarde"), 34.75)

    def test_bereken_resultaat_geeft_maximale_huurprijs_met_opslagen(self):
        # Beleidsboek bijlage 3 en 2.13.3: 114 punten is € 733,79, met 35%
        # rijksmonumentopslag € 990,62.
        resultaat = self._bereken_resultaat(
            monument=True,
            monument_soort="rijksmonument",
            huurovereenkomst_afgesloten_op=date(2024, 7, 1),
            vertrekken=[{"naam": RuimteNaam.WOONKAMER, "ruimte_m2": 100}],
            buitenruimten=[{"naam": RuimteNaam.PRIVE_BUITENRUIMTE, "ruimte_m2": 10}],
        ).as_dict()

        self.assertEqual(
            resultaat["maximale_huurprijs"],
            {"bedrag": 733.79, "met_opslagen": 990.62, "prijspeil": "2026-01-01"},
        )

    def test_bereken_resultaat_rekent_huurprijs_door_boven_250_punten(self):
        # Beleidsboek 2.1.6: elk punt boven 250 telt mee met het verschil tussen
        # 249 en 250 punten (€ 1.667,40 - € 1.660,54 = € 6,86).
        resultaat = self._bereken_resultaat(
            vertrekken=[{"naam": RuimteNaam.WOONKAMER, "ruimte_m2": 300}],
        )

        punten_boven_250 = int(resultaat.totaal_punten) - 250
        self.assertGreater(punten_boven_250, 0)
        self.assertEqual(
            resultaat.maximale_huurprijs.bedrag,
            Decimal("1667.40") + punten_boven_250 * Decimal("6.86"),
        )

    def test_bereken_resultaat_geeft_geen_huurprijs_zonder_huurprijstabel(self):
        Kengetal.objects.update(huurprijstabel_per_ingangsdatum={})

        resultaat = self._bereken_resultaat().as_dict()

        self.assertIsNone(resultaat["maximale_huurprijs"])
