from apps.cases.models import Case, CaseTheme
from apps.openzaak.tests.utils import ZakenBackendTestMixin
from apps.visits.models import Visit
from apps.workflow.models import CaseUserTask, CaseWorkflow
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core import management
from django.urls import reverse
from model_bakery import baker
from rest_framework import status
from rest_framework.test import APITestCase
from utils.unittest_helpers import (
    get_authenticated_client,
    get_authenticated_with_token_client,
    get_unauthenticated_client,
)

User = get_user_model()


class VisitApiTest(ZakenBackendTestMixin, APITestCase):
    def setUp(self):
        management.call_command("flush", verbosity=0, interactive=False)
        super().setUp()

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

        self.assertEqual(data["results"], [])

    def test_authenticated_get_filled(self):

        casetheme = baker.make(CaseTheme)
        case1 = baker.make(Case, theme=casetheme)
        caseworkflow = baker.make(CaseWorkflow, case=case1, id=7)
        baker.make(
            CaseUserTask,
            workflow=caseworkflow,
            case=case1,
            task_name="task_create_visit",
        )

        case2 = baker.make(Case, theme=casetheme)
        caseworkflow = baker.make(CaseWorkflow, case=case2, id=8)
        baker.make(
            CaseUserTask,
            workflow=caseworkflow,
            case=case2,
            task_name="task_create_visit",
        )
        baker.make(Visit, case=case1)
        baker.make(Visit, case=case2)

        url = reverse("visits-list")
        client = get_authenticated_client()

        response = client.get(url)
        data = response.json()

        self.assertEqual(len(data["results"]), 2)

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
        self.assertEqual(Visit.objects.count(), 0)

        casetheme = baker.make(CaseTheme)
        case = baker.make(Case, theme=casetheme)
        caseworkflow = baker.make(CaseWorkflow, case=case, id=2)
        baker.make(
            CaseUserTask,
            workflow=caseworkflow,
            case=case,
            task_name="task_create_visit",
        )

        url = reverse("visits-list")
        client = get_authenticated_client()

        data = {
            "authors": [{"email": "user@example.com"}],
            "start_time": "2021-03-31T17:17:52.126Z",
            "case": case.id,
            "task": "42",
            "top_visit_id": 42,
        }
        response = client.post(url, data=data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Visit.objects.count(), 1)

    def test_authenticated_user_create(self):
        # Should create users using the given email if they don't exist yet
        self.assertEqual(User.objects.count(), 0)

        casetheme = baker.make(CaseTheme)
        case = baker.make(Case, theme=casetheme)
        caseworkflow = baker.make(CaseWorkflow, case=case, id=3)
        baker.make(
            CaseUserTask,
            workflow=caseworkflow,
            case=case,
            task_name="task_create_visit",
        )

        # also tests case insensitive
        baker.make(User, email="usera@example.com")
        baker.make(User, email="userb@example.com")

        url = reverse("visits-list")
        client = get_authenticated_with_token_client(settings.SECRET_KEY_TOP_ZAKEN)

        data = {
            "authors": [{"email": "userA@example.com"}, {"email": "userB@example.com"}],
            "start_time": "2021-03-31T17:17:52.126Z",
            "case": case.id,
            "task": "42",
            "top_visit_id": 42,
        }

        response = client.post(url, data=data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.count(), 2)

        visit = Visit.objects.all()[0]
        self.assertEqual(len(visit.authors.all()), 2)

    def test_authenticated_visit_create_existing_users(self):
        # Should be able to process a visit using existing Users and their ids
        case = baker.make(Case)
        caseworkflow = baker.make(CaseWorkflow, case=case, id=4)
        baker.make(
            CaseUserTask,
            case=case,
            workflow=caseworkflow,
            task_name="task_create_visit",
        )
        user_a = baker.make(User, email="userA@example.com")
        user_b = baker.make(User, email="userB@example.com")

        url = reverse("visits-list")
        client = get_authenticated_with_token_client(settings.SECRET_KEY_TOP_ZAKEN)

        data = {
            "author_ids": [user_a.id, user_b.id],
            "start_time": "2021-03-31T17:17:52.126Z",
            "case": case.id,
            "task": "42",
            "top_visit_id": 42,
        }

        response = client.post(url, data=data, format="json")

        visit = Visit.objects.all()[0]
        self.assertEqual(len(visit.authors.all()), 2)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
