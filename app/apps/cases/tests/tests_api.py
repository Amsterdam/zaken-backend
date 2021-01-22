from apps.cases.models import Case, CaseReason, CaseTeam
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
        team = CaseTeam.objects.create(name="Foo Case Team")
        url = reverse("teams-reasons", kwargs={"pk": team.pk})

        client = get_authenticated_client()
        response = client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_authenticated_get_empty(self):
        team = CaseTeam.objects.create(name="Foo Case Team")
        url = reverse("teams-reasons", kwargs={"pk": team.pk})

        client = get_authenticated_client()
        response = client.get(url)
        data = response.json()

        self.assertEqual(data["results"], [])

    def test_authenticated_get_list(self):
        team = CaseTeam.objects.create(name="Foo Case Team")
        CaseReason.objects.create(name="Reason A", team=team)
        CaseReason.objects.create(name="Reason B", team=team)

        url = reverse("teams-reasons", kwargs={"pk": team.pk})

        client = get_authenticated_client()
        response = client.get(url)
        data = response.json()

        self.assertEqual(len(data["results"]), 2)


class CaseApiTest(APITestCase):
    def test_unauthenticated_post(self):
        url = reverse("cases-list")
        client = get_unauthenticated_client()
        response = client.post(url, {})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_authenticated_post_fail(self):
        url = reverse("cases-list")
        client = get_authenticated_client()
        response = client.post(url, {})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_authenticated_post_create(self):
        self.assertEquals(Case.objects.count(), 0)

        team = CaseTeam.objects.create(name="Foo Case Team")
        reason = CaseReason.objects.create(name="Reason A", team=team)

        url = reverse("cases-list")
        client = get_authenticated_client()
        response = client.post(
            url,
            {
                "description": "Foo",
                "team": team.pk,
                "reason": reason.pk,
                "address": {"bag_id": "foo bag ID"},
            },
            format="json",
        )

        self.assertEquals(response.status_code, status.HTTP_201_CREATED)
        self.assertEquals(Case.objects.count(), 1)

    def test_authenticated_post_create_fail_wrong_team(self):
        """ Should not be able to create a case if a wrong team ID is given """
        team = CaseTeam.objects.create(name="Foo Case Team")
        reason = CaseReason.objects.create(name="Reason A", team=team)

        url = reverse("cases-list")
        client = get_authenticated_client()
        response = client.post(
            url,
            {
                "description": "Foo",
                "team": 10,
                "reason": reason.pk,
                "address": {"bag_id": "foo bag ID"},
            },
            format="json",
        )

        self.assertEquals(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEquals(Case.objects.count(), 0)

    def test_authenticated_post_create_fail_wrong_reason(self):
        """ Should not be able to create a case if a wrong team ID is given """
        team = CaseTeam.objects.create(name="Foo Case Team")

        url = reverse("cases-list")
        client = get_authenticated_client()
        response = client.post(
            url,
            {
                "description": "Foo",
                "team": team.pk,
                "reason": 10,
                "address": {"bag_id": "foo bag ID"},
            },
            format="json",
        )

        self.assertEquals(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEquals(Case.objects.count(), 0)

    def test_authenticated_post_create_wrong_team_reason_relation(self):
        """ Request should fail if the CaseReason is not one of the given teams CaseReasons """
        self.assertEquals(Case.objects.count(), 0)

        team_a = CaseTeam.objects.create(name="Foo Case Team A")
        team_b = CaseTeam.objects.create(name="Foo Case Team B")
        reason = CaseReason.objects.create(name="Reason A", team=team_a)

        url = reverse("cases-list")
        client = get_authenticated_client()
        response = client.post(
            url,
            {
                "description": "Foo",
                "team": team_b.pk,
                "reason": reason.pk,
                "address": {"bag_id": "foo bag ID"},
            },
            format="json",
        )

        self.assertEquals(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEquals(Case.objects.count(), 0)
