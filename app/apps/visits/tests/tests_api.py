from apps.cases.models import Case
from apps.visits.models import Visit
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core import management
from django.urls import reverse
from model_bakery import baker
from rest_framework import status
from rest_framework.test import APITestCase

from app.utils.unittest_helpers import (
    get_authenticated_client,
    get_authenticated_with_token_client,
    get_test_user,
    get_unauthenticated_client,
)

User = get_user_model()


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

    def test_authenticated_post_201(self):
        self.assertEquals(Visit.objects.count(), 0)

        case = baker.make(Case)

        url = reverse("visits-list")
        client = get_authenticated_client()

        data = {
            "authors": [{"email": "user@example.com"}],
            "start_time": "2021-03-31T17:17:52.126Z",
            "case": case.id,
        }
        response = client.post(url, data=data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEquals(Visit.objects.count(), 1)

    def test_authenticated_user_create(self):
        # Should create users using the given email if they don't exist yet
        self.assertEquals(User.objects.count(), 0)

        case = baker.make(Case)

        url = reverse("visits-list")
        client = get_authenticated_with_token_client(settings.SECRET_KEY_TOP_ZAKEN)

        data = {
            "authors": [{"email": "userA@example.com"}, {"email": "userB@example.com"}],
            "start_time": "2021-03-31T17:17:52.126Z",
            "case": case.id,
        }
        response = client.post(url, data=data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEquals(User.objects.count(), 2)

    def test_authenticated_visit_create_existing_users(self):
        # Should be able to process a visit using existing Users and their ids
        case = baker.make(Case)
        user_a = baker.make(User, email="userA@example.com")
        user_b = baker.make(User, email="userB@example.com")

        url = reverse("visits-list")
        client = get_authenticated_with_token_client(settings.SECRET_KEY_TOP_ZAKEN)

        data = {
            "authors": [{"id": user_a.id}, {"id": user_b.id}],
            "start_time": "2021-03-31T17:17:52.126Z",
            "case": case.id,
        }
        response = client.post(url, data=data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
