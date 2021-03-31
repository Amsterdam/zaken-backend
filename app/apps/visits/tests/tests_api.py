from apps.visits.models import Visit
from django.core import management
from django.urls import reverse
from model_bakery import baker
from rest_framework import status
from rest_framework.test import APITestCase

from app.utils.unittest_helpers import (
    get_authenticated_client,
    get_test_user,
    get_unauthenticated_client,
)


class VisitApiTest(APITestCase):
    def setUp(self):
        management.call_command("flush", verbosity=0, interactive=False)

    def test_unauthenticated_get(self):
        url = reverse("visits-list")
        client = get_unauthenticated_client()
        response = client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_authenticated_get(self):
        url = reverse("visits-list")
        client = get_authenticated_client()
        response = client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_authenticated_get_empty(self):
        url = reverse("visits-list")
        client = get_authenticated_client()

        response = client.get(url)
        data = response.json()

        self.assertEquals(data["results"], [])

    def test_authenticated_get_filled(self):
        baker.make(Visit, _quantity=2)

        url = reverse("visits-list")
        client = get_authenticated_client()

        response = client.get(url)
        data = response.json()

        self.assertEquals(len(data["results"]), 2)

    def test_unauthenticated_post(self):
        url = reverse("visits-list")
        client = get_unauthenticated_client()
        response = client.post(url, data={}, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_authenticated_post_bad_request(self):
        url = reverse("visits-list")
        client = get_authenticated_client()
        response = client.post(url, data={}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
