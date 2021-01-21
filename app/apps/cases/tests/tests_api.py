from apps.cases.models import CaseReason, CaseTeam
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from app.utils.unittest_helpers import (
    get_authenticated_client,
    get_test_user,
    get_unauthenticated_client,
)


class CaseTeamApiTest(APITestCase):
    def test_unauthenticated_get(self):
        url = reverse("teams-list")
        client = get_unauthenticated_client()
        response = client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_authenticated_get(self):
        url = reverse("teams-list")
        client = get_authenticated_client()
        response = client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_authenticated_get_empty(self):
        url = reverse("teams-list")
        client = get_authenticated_client()

        response = client.get(url)
        data = response.json()

        self.assertEquals(data["results"], [])

    def test_authenticated_get_filled(self):
        CaseTeam.objects.create(name="Foo Case Team A")
        CaseTeam.objects.create(name="Foo Case Team B")

        url = reverse("teams-list")
        client = get_authenticated_client()

        response = client.get(url)
        data = response.json()

        self.assertEquals(len(data["results"]), 2)


class CaseTeamReasonApiTest(APITestCase):
    def test_unauthenticated_get(self):
        url = reverse("teams-reasons", kwargs={"pk": 1})

        client = get_unauthenticated_client()
        response = client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_authenticated_get_not_found(self):
        url = reverse("teams-reasons", kwargs={"pk": 99})

        client = get_authenticated_client()
        response = client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_authenticated_get(self):
        case_team = CaseTeam.objects.create(name="Foo Case Team")
        url = reverse("teams-reasons", kwargs={"pk": case_team.pk})

        client = get_authenticated_client()
        response = client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_authenticated_get_empty(self):
        case_team = CaseTeam.objects.create(name="Foo Case Team")
        url = reverse("teams-reasons", kwargs={"pk": case_team.pk})

        client = get_authenticated_client()
        response = client.get(url)
        data = response.json()

        self.assertEqual(data["results"], [])

    def test_authenticated_get_list(self):
        case_team = CaseTeam.objects.create(name="Foo Case Team")
        CaseReason.objects.create(name="Reason A", case_team=case_team)
        CaseReason.objects.create(name="Reason B", case_team=case_team)

        url = reverse("teams-reasons", kwargs={"pk": case_team.pk})

        client = get_authenticated_client()
        response = client.get(url)
        data = response.json()

        self.assertEqual(len(data["results"]), 2)
