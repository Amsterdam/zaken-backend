from apps.addresses.models import Address, District
from apps.cases.models import Case
from django.urls import reverse
from model_bakery import baker
from rest_framework import status
from rest_framework.test import APITestCase
from utils.unittest_helpers import get_authenticated_client, get_unauthenticated_client


class DataTeamCaseApiTest(APITestCase):
    @classmethod
    def setUpTestData(cls):
        # Maak district en adres voor tests
        cls.district = baker.make(District, name="Test District")
        cls.address = baker.make(
            Address,
            district=cls.district,
            street_name="Teststraat",
            number=1,
            postal_code="1234AB",
            lat=52.0,
            lng=5.0,
        )
        cls.case = baker.make(Case, address=cls.address)
        cls.url = reverse("data-cases-list")

    def setUp(self):
        self.auth_client = get_authenticated_client()
        self.unauth_client = get_unauthenticated_client()

    def test_unauthenticated_get_returns_401(self):
        response = self.unauth_client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_authenticated_get_returns_200(self):
        response = self.auth_client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertIn("results", data)

    def test_get_empty_and_filled_results(self):
        # Eerst alle cases verwijderen
        Case.objects.all().delete()
        response = self.auth_client.get(self.url)
        data = response.json()
        self.assertEqual(data["results"], [])

        # Nieuwe case toevoegen
        new_district = baker.make(District, name="Test District 2")
        new_address = baker.make(
            Address,
            district=new_district,
            street_name="Testlaan",
            number=2,
            postal_code="5678CD",
            lat=52.1,
            lng=5.1,
        )
        baker.make(Case, address=new_address)

        response = self.auth_client.get(self.url)
        data = response.json()
        self.assertEqual(len(data["results"]), 1)

    def test_serializer_contains_expected_fields(self):
        response = self.auth_client.get(self.url)
        data = response.json()
        case_data = data["results"][0]

        expected_case_fields = [
            "advertisements",
            "address",
            "project",
            "reason",
            "schedules",
            "state",
            "subjects",
            "tags",
            "theme",
        ]
        for field in expected_case_fields:
            self.assertIn(field, case_data)

        expected_address_fields = [
            "bag_id",
            "district",
            "lat",
            "lng",
            "number",
            "postal_code",
            "street_name",
        ]
        for field in expected_address_fields:
            self.assertIn(field, case_data["address"])

        self.assertIn("name", case_data["address"]["district"])
