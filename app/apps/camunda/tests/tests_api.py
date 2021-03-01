from apps.cases.models import Case, CaseState
from django.conf import settings
from django.core import management
from django.urls import reverse
from model_bakery import baker
from rest_framework import status
from rest_framework.test import APITestCase

from app.utils.unittest_helpers import (
    get_authenticated_with_token_client,
    get_unauthenticated_client,
)


class CamundaWorkerSetState(APITestCase):
    def setUp(self):
        management.call_command("flush", verbosity=0, interactive=False)

    def test_unauthenticated_post(self):
        url = reverse("camunda-workers-state")
        client = get_unauthenticated_client()
        response = client.post(url, data={}, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_authenticated_post_bad_request(self):
        url = reverse("camunda-workers-state")
        client = get_authenticated_with_token_client(settings.CAMUNDA_SECRET_KEY)
        response = client.post(url, data={}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_authenticated_post_201(self):
        url = reverse("camunda-workers-state")
        client = get_authenticated_with_token_client(settings.CAMUNDA_SECRET_KEY)
        case = baker.make(Case)

        response = client.post(
            url,
            data={"case_identification": case.identification, "state": "FOO"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_authenticated_post_current_states(self):
        """
        Test if a Case has correct open state after a post
        """
        case = baker.make(Case)
        current_states = list(case.get_current_states())
        self.assertListEqual(current_states, [])

        url = reverse("camunda-workers-state")
        client = get_authenticated_with_token_client(settings.CAMUNDA_SECRET_KEY)
        STATE_NAME = "FOO STATE NAME"

        client.post(
            url,
            data={"case_identification": case.identification, "state": STATE_NAME},
            format="json",
        )

        current_states = list(case.get_current_states())
        state = current_states[0]
        self.assertEquals(state.status.name, STATE_NAME)


class CamundaWorkerEndState(APITestCase):
    def setUp(self):
        management.call_command("flush", verbosity=0, interactive=False)

    def test_unauthenticated_post(self):
        url = reverse("camunda-workers-end-state")
        client = get_unauthenticated_client()
        response = client.post(url, data={}, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_authenticated_post_bad_request(self):
        url = reverse("camunda-workers-end-state")
        client = get_authenticated_with_token_client(settings.CAMUNDA_SECRET_KEY)
        response = client.post(url, data={}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_authenticated_post_bad_request_no_state(self):
        """ Should fail if the state doesn't exist """
        url = reverse("camunda-workers-end-state")
        client = get_authenticated_with_token_client(settings.CAMUNDA_SECRET_KEY)
        response = client.post(
            url, data={"state_identification": "non_existent_state_id"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_authenticated_post_success(self):
        """ Should succeed and the given state should have an end_date """
        state = baker.make(CaseState)
        self.assertIsNone(state.end_date)

        url = reverse("camunda-workers-end-state")
        client = get_authenticated_with_token_client(settings.CAMUNDA_SECRET_KEY)

        response = client.post(
            url, data={"state_identification": state.id}, format="json"
        )

        # Get the state again, which should be updated now
        state = CaseState.objects.get(id=state.id)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNotNone(state.end_date)
