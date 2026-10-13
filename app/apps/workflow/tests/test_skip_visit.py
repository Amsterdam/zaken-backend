from unittest.mock import patch

from apps.cases.models import Case, CaseTheme
from apps.visits.models import Visit
from apps.workflow.models import CaseUserTask, CaseWorkflow, GenericCompletedTask
from apps.workflow.serializers import CaseUserTaskWorkdflowSerializer
from django.core import management
from django.test import TestCase
from django.urls import reverse
from model_bakery import baker
from rest_framework import status
from rest_framework.test import APITestCase
from utils.unittest_helpers import get_authenticated_client

SKIP_VARIABLES = {
    "situation": {"value": "visit_skipped"},
    "visit_skipped_reason": {"value": "Politie is al ter plaatse geweest"},
}


def create_visit_workflow(theme_name="Ondermijning"):
    # A new workflow always gets the latest version, see case_workflow_pre_save
    theme = baker.make(CaseTheme, name=theme_name)
    case = baker.make(Case, theme=theme)
    return baker.make(
        CaseWorkflow,
        case=case,
        workflow_type=CaseWorkflow.WORKFLOW_TYPE_VISIT,
        data={},
    )


def create_additional_visit_workflow():
    theme = baker.make(CaseTheme, name="Ondermijning")
    case = baker.make(Case, theme=theme)
    return baker.make(
        CaseWorkflow,
        case=case,
        workflow_type=CaseWorkflow.WORKFLOW_TYPE_SUB,
        workflow_message_name="start_aanvullend_huisbezoek",
        data={},
    )


def start_until_task_create_visit(workflow):
    workflow.start()
    schedule_task = CaseUserTask.objects.get(
        workflow=workflow, task_name="task_create_schedule", completed=False
    )
    workflow.complete_user_task_and_create_new_user_tasks(schedule_task.task_id, {})
    return CaseUserTask.objects.get(
        workflow=workflow, task_name="task_create_visit", completed=False
    )


def remove_visit_skipped_option(task):
    # The form of visit versions before 8.3.0
    form = [f for f in task.form if f["name"] != "visit_skipped_reason"]
    for field in form:
        field["options"] = [
            o for o in field["options"] if o["value"] != "visit_skipped"
        ]
    CaseUserTask.objects.filter(id=task.id).update(form=form)
    task.refresh_from_db()


@patch("apps.workflow.models.task_complete_worflow.delay")
@patch("apps.workflow.signals.task_start_worflow.delay")
class SkipVisitWorkflowTest(TestCase):
    def setUp(self):
        management.call_command("flush", verbosity=0, interactive=False)
        super().setUp()

    def test_form_has_visit_skipped_option(self, *args):
        """The frontend shows the skip button based on this option"""
        task = start_until_task_create_visit(create_visit_workflow())
        situation = next(f for f in task.form if f["name"] == "situation")

        self.assertIn("visit_skipped", [o["value"] for o in situation["options"]])
        self.assertIn("visit_skipped_reason", [f["name"] for f in task.form])

    def test_serialized_form_has_visit_skipped_option(self, *args):
        task = start_until_task_create_visit(create_visit_workflow())
        form = CaseUserTaskWorkdflowSerializer(task).data["form"]
        situation = next(f for f in form if f["name"] == "situation")

        self.assertIn("visit_skipped", [o["value"] for o in situation["options"]])
        self.assertIn("visit_skipped_reason", [f["name"] for f in form])

    def test_visit_skipped_goes_to_debrief_after_no_visit(self, mock_start, mock_done):
        workflow = create_visit_workflow()
        task = start_until_task_create_visit(workflow)

        workflow.complete_user_task_and_create_new_user_tasks(
            task.task_id, SKIP_VARIABLES
        )

        workflow.refresh_from_db()
        self.assertTrue(workflow.completed)
        self.assertEqual(
            workflow.data.get("visit_next_step"), {"value": "debrief_after_no_visit"}
        )
        self.assertFalse(
            CaseUserTask.objects.filter(workflow=workflow, completed=False).exists()
        )
        mock_done.assert_called_once()

    def test_access_granted_still_goes_to_debrief_after_visit(self, *args):
        workflow = create_visit_workflow()
        task = start_until_task_create_visit(workflow)

        workflow.complete_user_task_and_create_new_user_tasks(
            task.task_id,
            {
                "situation": {"value": "access_granted"},
                "can_next_visit_go_ahead": {"value": False},
            },
        )

        workflow.refresh_from_db()
        self.assertEqual(
            workflow.data.get("visit_next_step"), {"value": "debrief_after_visit"}
        )


@patch("apps.workflow.models.task_complete_worflow.delay")
@patch("apps.workflow.signals.task_start_worflow.delay")
class SkipVisitApiTest(APITestCase):
    def setUp(self):
        management.call_command("flush", verbosity=0, interactive=False)
        super().setUp()

    def post_complete(self, task, variables):
        # Completes the task in the workflow without celery
        def complete_user_task(task_id, data, wait=False):
            task.workflow.complete_user_task_and_create_new_user_tasks(
                task.task_id, data
            )

        with patch.object(CaseWorkflow, "complete_user_task", complete_user_task):
            return get_authenticated_client().post(
                reverse("generic-tasks-complete-task"),
                data={
                    "case_user_task_id": task.id,
                    "case": task.case.id,
                    "variables": variables,
                },
                format="json",
            )

    def assert_not_completed(self, task, response):
        task.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(task.completed)
        self.assertEqual(GenericCompletedTask.objects.count(), 0)

    def test_skip_visit(self, *args):
        workflow = create_visit_workflow()
        task = start_until_task_create_visit(workflow)

        response = self.post_complete(task, SKIP_VARIABLES)

        task.refresh_from_db()
        workflow.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(task.completed)
        self.assertEqual(
            workflow.data.get("visit_next_step"),
            {"value": "debrief_after_no_visit"},
        )
        self.assertEqual(Visit.objects.count(), 0)

    def test_skip_visit_history(self, *args):
        task = start_until_task_create_visit(create_visit_workflow())

        self.post_complete(task, SKIP_VARIABLES)

        completed_task = GenericCompletedTask.objects.get()
        self.assertEqual(
            completed_task.variables["mapped_form_data"],
            {
                "situation": {
                    "label": "Wat is de situatie?",
                    "value": "Huisbezoek overgeslagen",
                },
                "visit_skipped_reason": {
                    "label": "Reden overslaan huisbezoek",
                    "value": "Politie is al ter plaatse geweest",
                },
            },
        )

    def test_skip_visit_without_reason(self, *args):
        task = start_until_task_create_visit(create_visit_workflow())

        for variables in (
            {"situation": {"value": "visit_skipped"}},
            {**SKIP_VARIABLES, "visit_skipped_reason": {"value": "  "}},
        ):
            self.assert_not_completed(task, self.post_complete(task, variables))

    def test_complete_visit_without_skip(self, *args):
        """A visit can only be completed by TOP"""
        task = start_until_task_create_visit(create_visit_workflow())

        for variables in ({}, {"situation": {"value": "access_granted"}}):
            self.assert_not_completed(task, self.post_complete(task, variables))

    def test_skip_visit_without_visit_skipped_option(self, *args):
        """Older visit versions have no visit_skipped flow"""
        task = start_until_task_create_visit(create_visit_workflow())
        remove_visit_skipped_option(task)

        self.assert_not_completed(task, self.post_complete(task, SKIP_VARIABLES))

    def test_skip_additional_visit(self, *args):
        """The additional visit in sub_workflow goes on to the debrief"""
        workflow = create_additional_visit_workflow()
        task = start_until_task_create_visit(workflow)
        self.assertEqual(task.name, "Doorgeven aanvullend huisbezoek TOP")

        response = self.post_complete(task, SKIP_VARIABLES)

        task.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(task.completed)
        self.assertEqual(
            list(
                CaseUserTask.objects.filter(
                    workflow=workflow, completed=False
                ).values_list("task_name", flat=True)
            ),
            ["task_create_debrief"],
        )
        self.assertEqual(Visit.objects.count(), 0)

    def test_visit_from_top_after_skip(self, *args):
        task = start_until_task_create_visit(create_visit_workflow())
        self.post_complete(task, SKIP_VARIABLES)

        response = get_authenticated_client().post(
            reverse("visits-list"),
            data={
                "authors": [{"email": "user@example.com"}],
                "start_time": "2021-03-31T17:17:52.126Z",
                "case": task.case.id,
                "task": "42",
                "top_visit_id": 42,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Visit.objects.count(), 0)
