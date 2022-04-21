"""
Tests for Debriefing models
"""
from apps.cases.models import Case
from apps.openzaak.tests.utils import ZakenBackendTestMixin
from apps.schedules.models import Action, DaySegment, Priority, Schedule, WeekSegment
from django.core import management
from django.urls import reverse
from model_bakery import baker
from rest_framework import status
from rest_framework.test import APITestCase

from app.utils.unittest_helpers import (
    get_authenticated_client,
    get_unauthenticated_client,
)


class ScheduleCreateAPITest(ZakenBackendTestMixin, APITestCase):
    def setUp(self):
        management.call_command("flush", verbosity=0, interactive=False)
        super().setUp()

    def test_unauthenticated_post(self):
        url = reverse("schedules-list")
        client = get_unauthenticated_client()
        response = client.post(url, {})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_authenticated_post_bad_request(self):
        url = reverse("schedules-list")
        client = get_authenticated_client()
        response = client.post(url, {})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_authenticated_post_create(self):
        self.assertEqual(Schedule.objects.count(), 0)

        action = baker.make(Action)
        week_segment = baker.make(WeekSegment)
        day_segment = baker.make(DaySegment)
        priority = baker.make(Priority)
        case = baker.make(Case)

        client = get_authenticated_client()
        url = reverse("schedules-list")

        response = client.post(
            url,
            {
                "action": action.id,
                "week_segment": week_segment.id,
                "day_segment": day_segment.id,
                "priority": priority.id,
                "case": case.id,
            },
            format="json",
        )

        self.assertEqual(Schedule.objects.count(), 1)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
