"""
Tests for Debriefing models
"""
from apps.debriefings.models import Debriefing
from apps.debriefings.tests.tests_helpers import DebriefingTestMixin
from apps.openzaak.tests.utils import ZakenBackendTestMixin
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from app.utils.unittest_helpers import (
    get_authenticated_client,
    get_unauthenticated_client,
)


class DebriefingCreateAPITest(ZakenBackendTestMixin, APITestCase, DebriefingTestMixin):
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
