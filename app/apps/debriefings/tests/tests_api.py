"""
Tests for Debriefing models
"""
from datetime import datetime

from apps.debriefings.models import Debriefing
from apps.debriefings.tests.tests_helpers import DebriefingTestMixin
from django.urls import reverse
from freezegun import freeze_time
from pytz import UTC
from rest_framework import status
from rest_framework.test import APITestCase

from app.utils.unittest_helpers import (
    get_authenticated_client,
    get_test_user,
    get_unauthenticated_client,
)


class DebriefingGetDetailAPITest(APITestCase, DebriefingTestMixin):
    def test_unauthenticated_get(self):
        url = reverse("debriefings-detail", kwargs={"pk": "foo"})
        client = get_unauthenticated_client()
        response = client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_authenticated_get_no_object(self):
        url = reverse("debriefings-detail", kwargs={"pk": "foo"})
        client = get_authenticated_client()
        response = client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_authenticated_get_object(self):
        debriefing = self.create_debriefing()
        url = reverse("debriefings-detail", kwargs={"pk": debriefing.id})
        client = get_authenticated_client()
        response = client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class DebriefingCreateAPITest(APITestCase, DebriefingTestMixin):
    def test_unauthenticated_post(self):
        url = reverse("debriefings-list")
        client = get_unauthenticated_client()
        response = client.post(url, {})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_authenticated_post_bad_request(self):
        url = reverse("debriefings-list")
        client = get_authenticated_client()
        response = client.post(url, {})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_authenticated_post_create(self):
        self.assertEqual(Debriefing.objects.count(), 0)
        case = self.create_case()

        data = {
            "violation": Debriefing.VIOLATION_ADDITIONAL_RESEARCH_REQUIRED,
            "feedback": "Hello World Feedback",
            "case": case.identification,
        }

        url = reverse("debriefings-list")
        client = get_authenticated_client()
        response = client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Debriefing.objects.count(), 1)


class DebriefingDeleteAPITest(APITestCase, DebriefingTestMixin):
    def test_unauthenticated_delete(self):
        url = reverse("debriefings-detail", kwargs={"pk": "foo"})
        client = get_unauthenticated_client()
        response = client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_authenticated_post_delete_request(self):
        url = reverse("debriefings-detail", kwargs={"pk": "foo"})
        client = get_authenticated_client()
        response = client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_authenticated_delete(self):
        debriefing = self.create_debriefing()
        self.assertEqual(Debriefing.objects.count(), 1)

        url = reverse("debriefings-detail", kwargs={"pk": debriefing.id})
        client = get_authenticated_client()
        response = client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Debriefing.objects.count(), 0)


class DebriefingUpdateAPITest(APITestCase, DebriefingTestMixin):
    def test_unauthenticated_update(self):
        url = reverse("debriefings-detail", kwargs={"pk": "foo"})
        client = get_unauthenticated_client()
        response = client.put(url, {})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_authenticated_update_bad_request(self):
        url = reverse("debriefings-detail", kwargs={"pk": "foo"})
        client = get_authenticated_client()
        response = client.put(url, {})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_authenticated_update(self):
        debriefing = self.create_debriefing()

        url = reverse("debriefings-detail", kwargs={"pk": debriefing.id})
        client = get_authenticated_client()

        UPDATED_FEEDBACK = debriefing.feedback + "UPDATED FEEDBACK"
        UPDATED_VIOLATION = Debriefing.VIOLATION_ADDITIONAL_RESEARCH_REQUIRED

        response = client.patch(
            url, {"feedback": UPDATED_FEEDBACK, "violation": UPDATED_VIOLATION}
        )

        debriefing = Debriefing.objects.all()[0]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(debriefing.feedback, UPDATED_FEEDBACK)
        self.assertEqual(debriefing.violation, UPDATED_VIOLATION)


class CaseDebriefingGetDetailAPITest(APITestCase, DebriefingTestMixin):
    def test_unauthenticated_get(self):
        url = reverse("cases-detail", kwargs={"identification": "foo"})
        client = get_unauthenticated_client()
        response = client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_authenticated_get_no_case(self):
        url = reverse("cases-detail", kwargs={"identification": "foo"})
        url += "/debriefings/"
        client = get_authenticated_client()
        response = client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_authenticated_get_no_debriefing(self):
        case = self.create_case()
        url = reverse("cases-detail", kwargs={"identification": case.identification})
        url += "debriefings/"

        client = get_authenticated_client()
        response = client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])

    def test_authenticated_get_debriefing(self):
        debriefing = self.create_debriefing()

        url = reverse(
            "cases-detail", kwargs={"identification": debriefing.case.identification}
        )
        url += "debriefings/"

        client = get_authenticated_client()
        response = client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_debriefing = response.json()[0]
        self.assertEqual(response_debriefing["case"], debriefing.case.identification)
        self.assertEqual(response_debriefing["author"], str(debriefing.author.id))
        self.assertEqual(response_debriefing["violation"], debriefing.violation)
        self.assertEqual(response_debriefing["feedback"], debriefing.feedback)
