from datetime import date

from apps.addresses.models import Address
from apps.puntenteller.models import Gebruikersinvoer, RuimteNaam
from apps.puntenteller.puntenteller import Puntenteller
from django.test import TestCase


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

        self.assertEqual(resultaat.rubrieken["badkamer"], 5.0)

    def test_bereken_resultaat_geeft_punten_voor_sanitair_extra_voorzieningen_rubriek(
        self,
    ):
        resultaat = self._bereken_resultaat(
            vertrekken=[
                {
                    "naam": RuimteNaam.BADKAMER,
                    "ruimte_m2": 0,
                    "douche": 1,
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

        self.assertEqual(resultaat.rubrieken["sanitair_extra_voorzieningen"], 4.0)

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

        self.assertEqual(resultaat.rubrieken["toilet"], 3.0)

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

        self.assertEqual(resultaat.rubrieken["sanitair_overig"], 1.0)

    def test_bereken_resultaat_geeft_punten_voor_woonvoorzieningen_handicap_rubriek(
        self,
    ):
        resultaat = self._bereken_resultaat(
            woonvoorziening_handicap=True,
            woonvoorziening_handicap_netto_investering=700,
        )

        self.assertEqual(resultaat.rubrieken["woonvoorzieningen_handicap"], 2.0)

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

        self.assertEqual(resultaat.rubrieken["keuken"], 5.75)

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

        self.assertEqual(resultaat.rubrieken["keuken"], 8.0)

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

        self.assertEqual(resultaat.rubrieken["vertrekken"], 10.0)

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

        self.assertEqual(resultaat.rubrieken["vertrekken"], 5.0)

    def test_bereken_resultaat_geeft_punten_voor_overige_ruimten_rubriek(self):
        resultaat = self._bereken_resultaat(
            overige_ruimten=[
                {
                    "naam": RuimteNaam.BERGING,
                    "ruimte_m2": 4,
                }
            ]
        )

        self.assertEqual(resultaat.rubrieken["overige_ruimten"], 3.0)

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

        self.assertEqual(resultaat.rubrieken["verwarming"], 4.0)

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

        self.assertEqual(resultaat.rubrieken["verkoeling"], 1.0)

    def test_bereken_resultaat_geeft_punten_voor_energieprestatie_rubriek(self):
        resultaat = self._bereken_resultaat(
            is_eengezinswoning=True,
            energielabel_klasse="A",
        )

        self.assertEqual(resultaat.rubrieken["energieprestatie"], 41.0)

    def test_bereken_resultaat_geeft_punten_voor_energieprestatie_index(self):
        resultaat = self._bereken_resultaat(
            is_eengezinswoning=True, energie_index="0.60"
        )

        self.assertEqual(resultaat.rubrieken["energieprestatie"], 52.0)

    def test_bereken_resultaat_geeft_punten_voor_energieprestatie_bouwjaar(self):
        resultaat = self._bereken_resultaat(is_eengezinswoning=True, bouwjaar=1995)

        self.assertEqual(resultaat.rubrieken["energieprestatie"], 22.0)

    def test_bereken_resultaat_geeft_punten_voor_buitenruimte_rubriek(self):
        resultaat = self._bereken_resultaat(
            buitenruimten=[
                {
                    "naam": RuimteNaam.PRIVE_BUITENRUIMTE,
                    "ruimte_m2": 10,
                }
            ]
        )

        self.assertEqual(resultaat.rubrieken["buitenruimte"], 5.5)

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

        self.assertEqual(resultaat.rubrieken["buitenruimte"], 3.75)

    def test_bereken_resultaat_trekt_vijf_punten_af_zonder_buitenruimte(self):
        resultaat = self._bereken_resultaat()

        self.assertEqual(resultaat.rubrieken["buitenruimte"], -5.0)

    def test_bereken_resultaat_geeft_punten_voor_parkeren_rubriek(self):
        resultaat = self._bereken_resultaat(
            parkeerruimten=[
                {
                    "naam": RuimteNaam.BUITENRUIMTE_PARKEERPLAATS,
                    "type": "gesloten_garage_bij_complex",
                }
            ]
        )

        self.assertEqual(resultaat.rubrieken["parkeren"], 9.0)

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

        self.assertEqual(resultaat.rubrieken["parkeren"], 4.5)

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

        self.assertEqual(resultaat.rubrieken["woz"], 19.25)

    def test_bereken_resultaat_past_woz_cap_toe_boven_maximum(self):
        resultaat = self._bereken_resultaat(
            vertrekken=[{"naam": RuimteNaam.WOONKAMER, "ruimte_m2": 200}],
            buitenruimten=[{"naam": RuimteNaam.PRIVE_BUITENRUIMTE, "ruimte_m2": 10}],
            woz_waarde=2000000,
            woz_peildatum_jaar=2025,
        )

        self.assertTrue(resultaat.correcties["woz_cap_toegepast"])
        self.assertEqual(resultaat.correcties["woz_cap_reden"], "33_procent_regel")
        self.assertEqual(resultaat.correcties["woz_na_cap"], 101.0)
        self.assertEqual(resultaat.totaal_punten_na_caps, 307.0)

    def test_bereken_resultaat_waardeert_woz_cap_minimaal_op_186_punten(self):
        resultaat = self._bereken_resultaat(
            vertrekken=[{"naam": RuimteNaam.WOONKAMER, "ruimte_m2": 92}],
            buitenruimten=[{"naam": RuimteNaam.PRIVE_BUITENRUIMTE, "ruimte_m2": 10}],
            woz_waarde=1200000,
            woz_peildatum_jaar=2025,
        )

        self.assertTrue(resultaat.correcties["woz_cap_toegepast"])
        self.assertTrue(resultaat.correcties["woz_minimale_waardering_186_toegepast"])
        self.assertEqual(resultaat.correcties["woz_na_cap"], 48.0)
        self.assertEqual(resultaat.totaal_punten_na_caps, 186.0)

    def test_bereken_resultaat_sluit_woz_cap_uit_onder_187_punten(self):
        resultaat = self._bereken_resultaat(
            vertrekken=[{"naam": RuimteNaam.WOONKAMER, "ruimte_m2": 90}],
            buitenruimten=[{"naam": RuimteNaam.PRIVE_BUITENRUIMTE, "ruimte_m2": 10}],
            woz_waarde=900000,
            woz_peildatum_jaar=2025,
        )

        self.assertFalse(resultaat.correcties["woz_cap_toegepast"])
        self.assertTrue(resultaat.correcties["woz_cap_uitgesloten"])
        self.assertEqual(
            resultaat.correcties["woz_cap_uitsluiting_reden"], "onder_187_punten"
        )
        self.assertFalse(resultaat.correcties["woz_minimale_waardering_186_toegepast"])

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

        self.assertTrue(resultaat.correcties["woz_cap_toegepast"])
        self.assertFalse(resultaat.correcties["woz_minimale_waardering_186_toegepast"])
        self.assertEqual(resultaat.correcties["woz_na_cap"], 48.0)
        self.assertEqual(resultaat.totaal_punten_na_caps, 146.0)

    def test_bereken_resultaat_verhoogt_zorgwoning_totaal_met_35_procent(self):
        resultaat = self._bereken_resultaat(
            zorgwoning=True,
            vertrekken=[{"naam": RuimteNaam.WOONKAMER, "ruimte_m2": 20}],
            buitenruimten=[{"naam": RuimteNaam.PRIVE_BUITENRUIMTE, "ruimte_m2": 20}],
        )

        self.assertTrue(resultaat.correcties["zorgwoning_toegepast"])
        self.assertEqual(
            self._bereken(
                zorgwoning=True,
                vertrekken=[{"naam": RuimteNaam.WOONKAMER, "ruimte_m2": 20}],
                buitenruimten=[
                    {"naam": RuimteNaam.PRIVE_BUITENRUIMTE, "ruimte_m2": 20}
                ],
            ),
            39.0,
        )

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

        self.assertTrue(resultaat.correcties["monument_toegepast"])
        self.assertEqual(
            resultaat.correcties["monument_correctie_type"], "extra_punten"
        )
        self.assertEqual(resultaat.correcties["monument_extra_punten"], 50.0)
        self.assertEqual(
            self._bereken(
                monument=True,
                monument_soort="rijksmonument",
                huurovereenkomst_afgesloten_op=date(2024, 6, 30),
                vertrekken=[{"naam": RuimteNaam.WOONKAMER, "ruimte_m2": 100}],
                buitenruimten=[
                    {"naam": RuimteNaam.PRIVE_BUITENRUIMTE, "ruimte_m2": 10}
                ],
            ),
            156.0,
        )

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

        self.assertTrue(resultaat.correcties["monument_toegepast"])
        self.assertEqual(
            resultaat.correcties["monument_correctie_type"], "huurprijsopslag"
        )
        self.assertEqual(resultaat.correcties["monument_huurprijsopslag_factor"], 1.35)
        self.assertEqual(
            self._bereken(
                monument=True,
                monument_soort="rijksmonument",
                huurovereenkomst_afgesloten_op=date(2024, 7, 1),
                vertrekken=[{"naam": RuimteNaam.WOONKAMER, "ruimte_m2": 100}],
                buitenruimten=[
                    {"naam": RuimteNaam.PRIVE_BUITENRUIMTE, "ruimte_m2": 10}
                ],
            ),
            142.0,
        )

    def test_bereken_resultaat_geeft_punten_voor_bijzondere_voorzieningen_rubriek(
        self,
    ):
        resultaat = self._bereken_resultaat(
            bijzondere_voorziening_intercom_met_beeld=True,
            bijzondere_voorziening_laadpalen=1,
        )

        self.assertEqual(resultaat.rubrieken["bijzondere_voorzieningen"], 3.0)
