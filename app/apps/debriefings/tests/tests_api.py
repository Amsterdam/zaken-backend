"""
Tests for Debriefing models
"""
from apps.debriefings.models import Debriefing
from apps.debriefings.tests.tests_helpers import DebriefingTestMixin
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from app.utils.unittest_helpers import (
    get_authenticated_client,
    get_test_user,
    get_unauthenticated_client,
)


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
            "case": case.id,
        }

        url = reverse("debriefings-list")
        client = get_authenticated_client()
        response = client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Debriefing.objects.count(), 1)


class CaseDebriefingGetDetailAPITest(APITestCase, DebriefingTestMixin):
    def test_unauthenticated_get(self):
        url = reverse("cases-detail", kwargs={"pk": 1})
        url += "debriefings/"
        client = get_unauthenticated_client()
        response = client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_authenticated_get_no_case(self):
        url = reverse("cases-detail", kwargs={"pk": 1})
        url += "debriefings/"
        client = get_authenticated_client()
        response = client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_authenticated_get_no_debriefing(self):
        case = self.create_case()
        url = reverse("cases-detail", kwargs={"pk": case.id})
        url += "debriefings/"

        client = get_authenticated_client()
        response = client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])

    def test_authenticated_get_debriefing(self):
        debriefing = self.create_debriefing()

        url = reverse("cases-detail", kwargs={"pk": debriefing.case.id})
        url += "debriefings/"

        client = get_authenticated_client()
        response = client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response_debriefing = response.json()[0]
        self.assertEqual(response_debriefing["case"], debriefing.case.id)
        self.assertEqual(response_debriefing["author"], str(debriefing.author.id))
        self.assertEqual(response_debriefing["violation"], debriefing.violation)
        self.assertEqual(response_debriefing["feedback"], debriefing.feedback)
