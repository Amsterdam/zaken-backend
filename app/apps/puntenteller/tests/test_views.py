from datetime import timedelta

from apps.addresses.models import Address
from apps.puntenteller.models import Gebruikersinvoer
from django.urls import reverse
from django.utils import timezone
from freezegun import freeze_time
from rest_framework import status
from rest_framework.test import APITestCase
from utils.unittest_helpers import (
    get_authenticated_client,
    get_test_user,
    get_unauthenticated_client,
)

BAG_ID = "bag-puntenteller-views-test"

PAYLOAD = {
    "energie": {"type": "bouwjaar", "waarde": "1970"},
    "is_eengezinswoning": False,
    "vertrekken": [],
    "overige_ruimten": [],
    "verkeersruimten": [],
    "buitenruimten": [],
    "parkeerruimten": [],
    "completed": False,
    "gebruiksoppervlakte": 60,
    "woz_waarde": 300000,
    "woz_peildatum_jaar": 2025,
}


# De minimum WOZ-waarde en de WOZ-kengetallen hangen af van de datum.
@freeze_time("2026-01-15")
class PuntentellerApiTest(APITestCase):
    fixtures = ["fixture.json"]

    def setUp(self):
        # Met een nummeraanduiding_id haalt het adres geen BAG-gegevens op.
        self.adres = Address.objects.create(
            bag_id=BAG_ID, nummeraanduiding_id="1234567890123456"
        )
        self.client = get_authenticated_client()

    def _lijst_url(self, bag_id=BAG_ID):
        return reverse("puntenteller-adressen-list", kwargs={"bag_id": bag_id})

    def _detail_url(self, gebruikersinvoer):
        return reverse(
            "puntenteller-puntentellingen-detail", kwargs={"pk": gebruikersinvoer.pk}
        )

    def _maak(self, **overrides):
        return Gebruikersinvoer.objects.create(adres=self.adres, **overrides)

    def test_niet_ingelogd_geeft_401(self):
        response = get_unauthenticated_client().get(self._lijst_url())
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_aanmaken_geeft_de_hele_puntentelling_terug(self):
        response = self.client.post(self._lijst_url(), PAYLOAD, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        data = response.json()
        gebruikersinvoer = Gebruikersinvoer.objects.get(pk=data["id"])
        self.assertEqual(gebruikersinvoer.adres, self.adres)
        self.assertEqual(gebruikersinvoer.author, get_test_user())
        self.assertFalse(data["completed"])
        self.assertEqual(data["author"]["id"], str(get_test_user().id))
        self.assertEqual(data["author"]["full_name"], get_test_user().full_name)
        self.assertIsNotNone(data["created"])
        self.assertEqual(data["punten"], data["punten_resultaat"]["totaal_punten"])

    def test_created_kan_niet_worden_meegestuurd(self):
        response = self.client.post(
            self._lijst_url(),
            {**PAYLOAD, "created": "2020-01-01T00:00:00Z"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.json()["created"].startswith("2026-01-15"))

    def test_lijst_geeft_de_puntentellingen_van_het_adres_nieuwste_eerst(self):
        oud = self._maak()
        nieuw = self._maak()
        Gebruikersinvoer.objects.filter(pk=oud.pk).update(
            created=timezone.now() - timedelta(days=1)
        )
        ander_adres = Address.objects.create(
            bag_id="ander-adres", nummeraanduiding_id="6543210987654321"
        )
        Gebruikersinvoer.objects.create(adres=ander_adres)

        response = self.client.get(self._lijst_url())

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual([item["id"] for item in response.json()], [nieuw.pk, oud.pk])

    def test_lijst_zonder_author_geeft_null(self):
        self._maak(author=None)

        response = self.client.get(self._lijst_url())

        self.assertIsNone(response.json()[0]["author"])

    def test_lijst_van_een_onbekend_adres_maakt_geen_adres_aan(self):
        response = self.client.get(self._lijst_url(bag_id="onbekend-adres"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), [])
        self.assertFalse(Address.objects.filter(bag_id="onbekend-adres").exists())

    def test_wijzigen_van_een_concept_rekent_opnieuw(self):
        gebruikersinvoer = self._maak(gebruiksoppervlakte=0)
        voor = self.client.get(self._detail_url(gebruikersinvoer)).json()

        response = self.client.patch(
            self._detail_url(gebruikersinvoer), PAYLOAD, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertNotEqual(data["punten_resultaat"], voor["punten_resultaat"])
        self.assertEqual(data["punten"], data["punten_resultaat"]["totaal_punten"])

    def test_een_concept_definitief_maken(self):
        gebruikersinvoer = self._maak(woz_waarde=123456)

        response = self.client.patch(
            self._detail_url(gebruikersinvoer), {"completed": True}, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        gebruikersinvoer.refresh_from_db()
        self.assertTrue(gebruikersinvoer.completed)
        # Een gedeeltelijke wijziging laat de rest staan.
        self.assertEqual(gebruikersinvoer.woz_waarde, 123456)

    def test_een_afgeronde_puntentelling_kan_weer_worden_gewijzigd(self):
        gebruikersinvoer = self._maak(completed=True)

        response = self.client.patch(
            self._detail_url(gebruikersinvoer), {"completed": False}, format="json"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        gebruikersinvoer.refresh_from_db()
        self.assertFalse(gebruikersinvoer.completed)

    def test_een_concept_verwijderen(self):
        gebruikersinvoer = self._maak()

        response = self.client.delete(self._detail_url(gebruikersinvoer))

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(
            Gebruikersinvoer.objects.filter(pk=gebruikersinvoer.pk).exists()
        )

    def test_een_afgeronde_puntentelling_kan_worden_verwijderd(self):
        gebruikersinvoer = self._maak(completed=True)

        response = self.client.delete(self._detail_url(gebruikersinvoer))

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(
            Gebruikersinvoer.objects.filter(pk=gebruikersinvoer.pk).exists()
        )
