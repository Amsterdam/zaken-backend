from datetime import date
from decimal import Decimal

from apps.addresses.models import Address
from apps.puntenteller.models import Gebruikersinvoer, RuimteNaam
from apps.puntenteller.puntenteller import Puntenteller
from django.test import TestCase
from freezegun import freeze_time

# Regressieset: woningen die ook in de rekenmodule van de Huurcommissie zijn
# doorgerekend. De verwachte punten komen uit die rekenmodule. Waar we bewust
# afwijken staat dat bij de test.

KEUKEN = {
    "naam": RuimteNaam.KEUKEN,
    "ruimte_m2": 7,
    "verwarmd": True,
    "aanrechtlengte_meters": "1.50",
    "inbouw_afzuiginstallatie": 1,
    "inbouw_kookplaat_inductie": 1,
    "inbouw_koelkast": 1,
    "inbouw_oven_elektrisch": 5,
    "inbouw_oven_gas": 5,
    "inbouw_magnetron": 5,
    "inbouw_vaatwasmachine": 5,
    "extra_kastruimte": 5,
    "eenhandsmengkraan": 1,
}
WOONKAMER = {
    "naam": RuimteNaam.WOONKAMER,
    "ruimte_m2": 20,
    "verwarmd": True,
    "gekoeld": True,
}
BADKAMER = {
    "naam": RuimteNaam.BADKAMER,
    "ruimte_m2": 15,
    "verwarmd": True,
    "toilet_hangend": 1,
    "baddouche": 1,
}
# "Bad, douche of wastafel in andere ruimte" bij de Huurcommissie.
BAD_IN_ANDERE_RUIMTE = {
    "naam": RuimteNaam.BADKAMER,
    "ruimte_m2": 0,
    "toilet_hangend": 1,
    "wastafel": 5,
    "bad": 1,
    "volledige_afscheiding_douche": 1,
    "kastruimte": 5,
    "stopcontacten": 5,
}
TOILETRUIMTE = {
    "naam": RuimteNaam.TOILETRUIMTE,
    "ruimte_m2": 4,
    "verwarmd": True,
    "toilet_hangend": 1,
}
ZOLDER_ZONDER_VASTE_TRAP = {
    "naam": RuimteNaam.ZOLDER,
    "ruimte_m2": 15,
    "heeft_vaste_trap": False,
}
ACHTERTUIN = {"naam": RuimteNaam.PRIVE_BUITENRUIMTE, "ruimte_m2": 72}
RIJKSMONUMENT_VOOR_WBH = {
    "monument": True,
    "monument_soort": "rijksmonument",
    "huurovereenkomst_afgesloten_op": date(2024, 6, 30),
}


@freeze_time("2026-01-15")
class HuurcommissieTest(TestCase):
    fixtures = ["fixture.json"]

    def setUp(self):
        self.adres = Address.objects.create(
            bag_id="bag-huurcommissie-test",
            nummeraanduiding_id="1234567890123456",
        )

    def _bereken_resultaat(self, **invoer):
        gebruikersinvoer = Gebruikersinvoer.objects.create(adres=self.adres, **invoer)
        return Puntenteller(gebruikersinvoer).bereken_resultaat()

    def _punten(self, resultaat, naam):
        return resultaat.rubriek(naam).punten

    def _zorgwoning_met_zolder(self, **extra):
        return self._bereken_resultaat(
            **RIJKSMONUMENT_VOOR_WBH,
            zorgwoning=True,
            is_eengezinswoning=True,
            energie_index=Decimal("1.5"),
            woz_waarde=316000,
            woz_peildatum_jaar=2025,
            bijzondere_voorziening_intercom_met_beeld=True,
            vertrekken=[
                WOONKAMER,
                KEUKEN,
                {**BADKAMER, "volledige_afscheiding_douche": 1},
                BAD_IN_ANDERE_RUIMTE,
            ],
            overige_ruimten=[TOILETRUIMTE, ZOLDER_ZONDER_VASTE_TRAP],
            buitenruimten=[ACHTERTUIN],
            **extra,
        )

    def test_rijksmonument_met_afgetopte_woz(self):
        # Huurcommissie: 210 punten. De 50 rijksmonumentpunten tellen mee in de
        # WOZ-cap: (90,75 + 50) x 33/67 = 69,33, wordt 69 WOZ-punten.
        resultaat = self._bereken_resultaat(
            **RIJKSMONUMENT_VOOR_WBH,
            is_eengezinswoning=True,
            energielabel_klasse="G",
            woz_waarde=3160000,
            woz_peildatum_jaar=2025,
            bijzondere_voorziening_intercom_met_beeld=True,
            vertrekken=[WOONKAMER, KEUKEN, BADKAMER],
            overige_ruimten=[{**TOILETRUIMTE, "wastafel": 1}],
            buitenruimten=[ACHTERTUIN],
        )

        self.assertEqual(self._punten(resultaat, "Oppervlakte vertrekken"), 42)
        self.assertEqual(self._punten(resultaat, "Oppervlakte overige ruimten"), 3)
        self.assertEqual(self._punten(resultaat, "Verwarming en verkoeling"), 8)
        self.assertEqual(self._punten(resultaat, "Energieprestatie"), 0)
        self.assertEqual(self._punten(resultaat, "Keuken"), 8)
        self.assertEqual(self._punten(resultaat, "Sanitair"), Decimal("14.5"))
        self.assertEqual(self._punten(resultaat, "Buitenruimten"), 15)
        self.assertEqual(self._punten(resultaat, "WOZ-waarde"), 69)
        self.assertEqual(self._punten(resultaat, "Rijksmonument"), 50)
        self.assertEqual(resultaat.totaal_punten, 210)

    def test_zorgwoning_rijksmonument(self):
        # Huurcommissie: 285 punten, met sanitair 31,75 en zorgwoning 60,90.
        # Afwijking: de Huurcommissie telt de douche-afscheiding in de badkamer
        # zonder wastafel mee (1,25). Wij volgen beleidsboek 2.6.2, dus sanitair
        # 30,5, zorgwoning 35% van 172,75 = 60,46, wordt 60,5, en totaal 284.
        resultaat = self._zorgwoning_met_zolder()

        self.assertEqual(
            self._punten(resultaat, "Oppervlakte overige ruimten"), Decimal("9.25")
        )
        self.assertEqual(self._punten(resultaat, "Energieprestatie"), 22)
        self.assertEqual(self._punten(resultaat, "Sanitair"), Decimal("30.5"))
        self.assertEqual(self._punten(resultaat, "Gemeenschappelijke ruimten"), 0)
        self.assertEqual(self._punten(resultaat, "WOZ-waarde"), 38)
        self.assertEqual(self._punten(resultaat, "Zorgwoning"), Decimal("60.5"))
        self.assertEqual(resultaat.totaal_punten, 284)

    def test_zorgwoning_rijksmonument_met_gedeelde_garages(self):
        # Huurcommissie: 293 punten, met parkeren 9, WOZ 34,75 (73 m²) en
        # zorgwoning 62,91. Zelfde afwijking in sanitair als hierboven, dus bij
        # ons zorgwoning 35% van 178,5 = 62,48, wordt 62,5, en totaal 291.
        resultaat = self._zorgwoning_met_zolder(
            parkeerruimten=[
                {
                    "naam": RuimteNaam.BUITENRUIMTE_PARKEERPLAATS,
                    "aantal_gesloten_garage_bij_complex": 20,
                    "aantal_adressen_met_toegang_en_gebruiksrecht": 20,
                }
            ],
        )

        self.assertEqual(self._punten(resultaat, "Parkeren"), 9)
        self.assertEqual(self._punten(resultaat, "WOZ-waarde"), Decimal("34.75"))
        self.assertEqual(self._punten(resultaat, "Zorgwoning"), Decimal("62.5"))
        self.assertEqual(resultaat.totaal_punten, 291)

    def test_zorgwoning_met_afgetopte_woz(self):
        # Huurcommissie: zorgtoeslag over de WOZ vóór de cap, 35% x (48 + 422,25)
        # = 164,59, wordt 164,5. De cap komt als laatste en telt de toeslag mee:
        # 33/67 x (48 + 164,5) = 104,66, wordt 104. Totaal 316,5.
        # Afwijking: de Huurcommissie rondt 316,5 af op 316, wij volgen
        # beleidsboek 2.1.5 (vanaf 0,5 naar boven) en komen op 317.
        resultaat = self._bereken_resultaat(
            zorgwoning=True,
            is_eengezinswoning=True,
            energielabel_klasse="G",
            woz_waarde=3160000,
            woz_peildatum_jaar=2025,
            vertrekken=[
                {"naam": RuimteNaam.WOONKAMER, "ruimte_m2": 20, "verwarmd": True},
                {
                    "naam": RuimteNaam.KEUKEN,
                    "ruimte_m2": 30,
                    "verwarmd": True,
                    "aanrechtlengte_meters": "2.50",
                    "inbouw_afzuiginstallatie": 5,
                    "inbouw_kookplaat_inductie": 5,
                    "inbouw_kookplaat_keramisch": 5,
                    "inbouw_kookplaat_gas": 5,
                    "inbouw_magnetron": 1,
                },
            ],
        )

        self.assertEqual(self._punten(resultaat, "Keuken"), 14)
        self.assertEqual(self._punten(resultaat, "Zorgwoning"), Decimal("164.5"))
        self.assertEqual(self._punten(resultaat, "WOZ-waarde"), 104)
        self.assertEqual(resultaat.totaal_punten, 317)

    def test_woonvoorzieningen_handicap(self):
        # Huurcommissie: 3 punten voor € 1.234 (1.234 / 332 = 3,72).
        resultaat = self._bereken_resultaat(
            woonvoorziening_handicap=True,
            woonvoorziening_handicap_netto_investering=1234,
        )

        self.assertEqual(
            self._punten(resultaat, "Woonvoorzieningen voor personen met een handicap"),
            3,
        )
