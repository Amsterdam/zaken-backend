import datetime

from apps.addresses.models import Address
from apps.cases.models import Case
from apps.openzaak.tests.utils import ZakenBackendTestMixin
from django.core import management
from django.urls import reverse
from model_bakery import baker
from rest_framework import status
from rest_framework.test import APITestCase

from app.utils.unittest_helpers import (
    get_authenticated_client,
    get_unauthenticated_client,
)


class AddressCasesApiTest(ZakenBackendTestMixin, APITestCase):
    def setUp(self):
        management.call_command("flush", verbosity=0, interactive=False)
        super().setUp()

    def test_unauthenticated_get(self):
        url = reverse("addresses-cases", kwargs={"bag_id": "foo"})
        client = get_unauthenticated_client()
        response = client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_authenticated_get_no_address(self):
        """
        If the Address does not exist, the endpoint should return an empty results list
        """
        url = reverse("addresses-cases", kwargs={"bag_id": "foo"})
        client = get_authenticated_client()
        response = client.get(url)
        response = client.get(url)
        data = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(data["results"], [])

    def test_authenticated_get_no_results(self):
        """
        If the Address exists but not cases use it, the endpoint should return an empty results list
        """
        BAG_ID = "foo"
        baker.make(Address, bag_id=BAG_ID)

        url = reverse("addresses-cases", kwargs={"bag_id": BAG_ID})
        client = get_authenticated_client()
        response = client.get(url)
        data = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(data["results"], [])

    def test_authenticated_get_results(self):
        BAG_ID = "foo"
        NUMBER_OF_CASES = 5

        address = baker.make(Address, bag_id=BAG_ID)
        baker.make(Case, address=address, _quantity=NUMBER_OF_CASES)

        url = reverse("addresses-cases", kwargs={"bag_id": BAG_ID})
        client = get_authenticated_client()
        response = client.get(url)
        data = response.json()

        self.assertEqual(len(data["results"]), NUMBER_OF_CASES)

    def test_authenticated_get_open_cases_results(self):
        BAG_ID = "foo"
        NUMBER_OF_CLOSED_CASES = 5
        NUMBER_OF_OPEN_CASES = 3

        address = baker.make(Address, bag_id=BAG_ID)
        baker.make(
            Case,
            address=address,
            end_date=datetime.datetime.now(),
            _quantity=NUMBER_OF_CLOSED_CASES,
        )
        baker.make(Case, address=address, end_date=None, _quantity=NUMBER_OF_OPEN_CASES)

        url = reverse("addresses-cases", kwargs={"bag_id": BAG_ID})
        client = get_authenticated_client()
        response = client.get(url + "?open_cases=true")
        data = response.json()

        self.assertEqual(len(data["results"]), NUMBER_OF_OPEN_CASES)

    def test_authenticated_get_closed_cases_results(self):
        BAG_ID = "foo"
        NUMBER_OF_CLOSED_CASES = 5
        NUMBER_OF_OPEN_CASES = 3

        address = baker.make(Address, bag_id=BAG_ID)
        baker.make(
            Case,
            address=address,
            end_date=datetime.datetime.now(),
            _quantity=NUMBER_OF_CLOSED_CASES,
        )
        baker.make(Case, address=address, end_date=None, _quantity=NUMBER_OF_OPEN_CASES)

        url = reverse("addresses-cases", kwargs={"bag_id": BAG_ID})
        client = get_authenticated_client()
        response = client.get(url + "?open_cases=false")
        data = response.json()

        self.assertEqual(len(data["results"]), NUMBER_OF_CLOSED_CASES)
