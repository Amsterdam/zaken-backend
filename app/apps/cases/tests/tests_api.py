from apps.cases.const import PLAN_VISIT
from apps.cases.models import Case, CaseReason, CaseTeam
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


class CaseTeamApiTest(APITestCase):
    def setUp(self):
        management.call_command("flush", verbosity=0, interactive=False)

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
        baker.make(CaseTeam, _quantity=2)

        url = reverse("teams-list")
        client = get_authenticated_client()

        response = client.get(url)
        data = response.json()

        self.assertEquals(len(data["results"]), 2)


class CaseTeamReasonApiTest(APITestCase):
    def setUp(self):
        management.call_command("flush", verbosity=0, interactive=False)

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
        team = baker.make(CaseTeam)
        url = reverse("teams-reasons", kwargs={"pk": team.pk})

        client = get_authenticated_client()
        response = client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_authenticated_get_empty(self):
        team = baker.make(CaseTeam)
        url = reverse("teams-reasons", kwargs={"pk": team.pk})

        client = get_authenticated_client()
        response = client.get(url)
        data = response.json()

        self.assertEqual(data["results"], [])

    def test_authenticated_get_list(self):
        team = baker.make(CaseTeam)
        baker.make(CaseReason, team=team, _quantity=2)

        url = reverse("teams-reasons", kwargs={"pk": team.pk})

        client = get_authenticated_client()
        response = client.get(url)
        data = response.json()

        self.assertEqual(len(data["results"]), 2)


class CaseApiTest(APITestCase):
    def setUp(self):
        management.call_command("flush", verbosity=0, interactive=False)

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

        team = baker.make(CaseTeam)
        reason = baker.make(CaseReason, team=team)

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
        team = baker.make(CaseTeam)
        reason = baker.make(CaseReason, team=team)

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
        team = baker.make(CaseTeam)

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

        team_a = baker.make(CaseTeam)
        team_b = baker.make(CaseTeam)
        reason = baker.make(CaseReason, team=team_a)

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

    def test_authenticated_post_create_author(self):
        """
        The author of the case should automatically be set to the authenticated user who made the POST request
        """
        self.assertEquals(Case.objects.count(), 0)

        team = baker.make(CaseTeam)
        reason = baker.make(CaseReason, team=team)

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

        test_user = get_test_user()
        case = Case.objects.get(id=response.data["id"])

        self.assertEquals(case.author, test_user)

    def test_authenticated_post_create_state(self):
        """
        A initial state should be set whenever a case is created
        """
        self.assertEquals(Case.objects.count(), 0)

        team = baker.make(CaseTeam)
        reason = baker.make(CaseReason, team=team)

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

        case = Case.objects.get(id=response.data["id"])
        state = case.get_current_state()

        self.assertEquals(state.status.name, PLAN_VISIT)
