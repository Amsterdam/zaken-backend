import datetime

from apps.addresses.models import Address
from apps.cases.models import Case
from django.core import management
from django.urls import reverse
from model_bakery import baker
from rest_framework import status
from rest_framework.test import APITestCase

from app.utils.unittest_helpers import (
    get_authenticated_client,
    get_unauthenticated_client,
)


class AddressCasesApiTest(APITestCase):
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

    def test_authenticated_get_includes_sensitive_cases(self):
        """
        DELIBERATE DESIGN: users without the `users.access_sensitive_dossiers`
        permission should still see THAT sensitive cases exist on an address
        (so they know what is going on at the address), but only with the
        limited field set of CaseAddressSerializer. Detail access to
        sensitive cases remains restricted via CaseViewSet.
        """
        BAG_ID = "foo"

        address = baker.make(Address, bag_id=BAG_ID)
        baker.make(Case, address=address, sensitive=True)
        baker.make(Case, address=address, sensitive=False)

        url = reverse("addresses-cases", kwargs={"bag_id": BAG_ID})
        client = get_authenticated_client()
        response = client.get(url)
        data = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(data["results"]), 2)

    def test_authenticated_get_returns_only_limited_fields(self):
        """
        The address endpoint must never expose the full CaseSerializer
        representation. Only this limited field set is allowed, so that
        details of sensitive cases do not leak to users without the
        `users.access_sensitive_dossiers` permission. Do not add fields
        here without reviewing what they reveal about sensitive cases.
        """
        BAG_ID = "foo"
        EXPECTED_FIELDS = {
            "id",
            "advertisements",
            "start_date",
            "end_date",
            "theme",
            "workflows",
            "reason",
        }

        address = baker.make(Address, bag_id=BAG_ID)
        baker.make(Case, address=address, sensitive=True)

        url = reverse("addresses-cases", kwargs={"bag_id": BAG_ID})
        client = get_authenticated_client()
        response = client.get(url)
        data = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(set(data["results"][0].keys()), EXPECTED_FIELDS)
