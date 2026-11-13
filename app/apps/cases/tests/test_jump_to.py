from unittest.mock import patch

from apps.addresses.models import Address
from apps.cases.models import Case, CaseReason, CaseTheme
from django.core import management
from django.urls import reverse
from model_bakery import baker
from rest_framework import status
from rest_framework.test import APIClient, APITestCase
from utils.unittest_helpers import get_authenticated_client, get_test_user

BAG_ID = "jump_to bag ID"


@patch("apps.workflow.tasks.task_create_main_worflow_for_case.delay")
class CaseCreateJumpToApiTest(APITestCase):
    """jump_to on POST /cases/ is passed on, once, to the main workflow"""

    def setUp(self):
        management.call_command("flush", verbosity=0, interactive=False)
        super().setUp()
        # An address with a nummeraanduiding_id doesn't call the BAG API on save
        baker.make(Address, bag_id=BAG_ID, nummeraanduiding_id="0363200000000001")
        self.theme = baker.make(CaseTheme)
        self.reason = baker.make(CaseReason, theme=self.theme)

    def post_case(self, **extra):
        return get_authenticated_client().post(
            reverse("cases-list"),
            {
                "description": "Foo",
                "theme_id": self.theme.pk,
                "reason_id": self.reason.pk,
                "bag_id": BAG_ID,
                **extra,
            },
            format="json",
        )

    def test_create_with_jump_to(self, create_main_workflow):
        response = self.post_case(jump_to="summon")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        case = Case.objects.get()
        create_main_workflow.assert_called_once_with(
            case_id=case.id, data={"jump_to": "summon"}
        )

    def test_unoccupied_only_for_the_theme_leegstand(self, create_main_workflow):
        client = APIClient()
        client.force_authenticate(user=get_test_user())

        def post_case(**extra):
            return client.post(
                reverse("cases-list"),
                {
                    "description": "Foo",
                    "theme_id": self.theme.pk,
                    "reason_id": self.reason.pk,
                    "bag_id": BAG_ID,
                    **extra,
                },
                format="json",
            )

        # The theme of setUp is not Leegstand.
        response = post_case(jump_to="unoccupied")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("jump_to", response.json())
        create_main_workflow.assert_not_called()

        self.theme.name = "Leegstand"
        self.theme.save()
        response = post_case(jump_to="unoccupied")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_without_jump_to(self, create_main_workflow):
        response = self.post_case()

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        create_main_workflow.assert_called_once_with(
            case_id=Case.objects.get().id, data={}
        )

    def test_create_with_not_allowed_jump_to(self, create_main_workflow):
        response = self.post_case(jump_to="decision")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("jump_to", response.json())
        self.assertFalse(Case.objects.exists())
        create_main_workflow.assert_not_called()

    def test_update_ignores_jump_to(self, create_main_workflow):
        self.post_case()
        case = Case.objects.get()

        response = get_authenticated_client().patch(
            reverse("cases-detail", args=[case.id]),
            {"description": "Bar", "jump_to": "summon"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Only the create triggered the main workflow
        create_main_workflow.assert_called_once()


@patch("apps.workflow.tasks.task_create_main_worflow_for_case.delay")
class CaseInitialWorkflowDataTest(APITestCase):
    def setUp(self):
        management.call_command("flush", verbosity=0, interactive=False)
        super().setUp()

    def test_initial_workflow_data_as_constructor_argument(self, create_main_workflow):
        theme = baker.make(CaseTheme)
        case = Case.objects.create(
            theme=theme,
            reason=baker.make(CaseReason, theme=theme),
            initial_workflow_data={"jump_to": "debrief"},
        )

        create_main_workflow.assert_called_once_with(
            case_id=case.id, data={"jump_to": "debrief"}
        )
        # Not stored: a case loaded from the database has none
        self.assertEqual(Case.objects.get(id=case.id).initial_workflow_data, {})
