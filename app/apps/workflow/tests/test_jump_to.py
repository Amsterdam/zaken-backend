from unittest.mock import patch

from apps.cases.models import Case, CaseReason, CaseTheme
from apps.workflow.jump_to import (
    JUMP_EVENT_DESCRIPTION,
    JUMP_EVENT_TASK_NAME,
    JUMP_TO_KEY,
    JUMP_TO_TARGETS,
    JUMPED_TO_SUBWORKFLOW_KEY,
    get_jump_to_routing_data,
    get_jump_to_targets,
)
from apps.workflow.models import CaseUserTask, CaseWorkflow, GenericCompletedTask
from django.contrib.auth import get_user_model
from django.core import management
from django.test import TestCase
from django.urls import reverse
from model_bakery import baker
from rest_framework import status
from rest_framework.test import APITestCase
from SpiffWorkflow import TaskState
from utils.unittest_helpers import get_authenticated_client, get_unauthenticated_client

# First user task of each allowed target, when started without any form data
FIRST_TASKS = {
    "summon": "task_create_concept_summons",
    "unoccupied": "task_opstellen_aanschrijving_eigenaar",
    "debrief": "task_create_debrief",
}


def create_case(author=None):
    theme, _ = CaseTheme.objects.get_or_create(name="Kamerverhuur")
    reason, _ = CaseReason.objects.get_or_create(name="Eigen onderzoek", theme=theme)
    return baker.make(Case, theme=theme, reason=reason, author=author)


def create_director(case, data=None):
    return baker.make(
        CaseWorkflow,
        case=case,
        workflow_type=CaseWorkflow.WORKFLOW_TYPE_DIRECTOR,
        main_workflow=True,
        workflow_message_name="main_process",
        data=data or {},
    )


def waiting_messages(workflow):
    wf = workflow.get_or_restore_workflow_state()
    return [
        getattr(getattr(t.task_spec, "event_definition", None), "name", None)
        for t in wf.get_tasks(state=TaskState.WAITING)
    ]


class JumpToTargetsTest(TestCase):
    def test_targets_match_first_tasks(self):
        """Every allowed target is covered by the tests below"""
        self.assertEqual(set(JUMP_TO_TARGETS), set(FIRST_TASKS))

    def test_get_jump_to_targets(self):
        self.assertIn(
            {"value": "summon", "label": "Aanschrijving"}, get_jump_to_targets()
        )
        self.assertNotIn("decision", [t["value"] for t in get_jump_to_targets()])

    def test_routing_data_is_a_copy(self):
        get_jump_to_routing_data("summon")["debrief_next_step"]["value"] = "changed"
        self.assertEqual(
            get_jump_to_routing_data("summon"),
            {"debrief_next_step": {"value": "summon"}},
        )


class AllowedJumpWorkflowsApiTest(APITestCase):
    def test_unauthenticated_get(self):
        response = get_unauthenticated_client().get(
            reverse("cases-allowed-jump-workflows")
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_targets(self):
        response = get_authenticated_client().get(
            reverse("cases-allowed-jump-workflows")
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json(), get_jump_to_targets())


@patch("apps.workflow.models.task_start_subworkflow.delay")
@patch("apps.workflow.signals.task_start_worflow.delay")
@patch("apps.workflow.tasks.task_create_main_worflow_for_case.delay")
class JumpToDirectorTest(TestCase):
    def setUp(self):
        management.call_command("flush", verbosity=0, interactive=False)
        super().setUp()

    def test_director_jumps_to_each_target(self, _, __, start_subworkflow):
        for target in JUMP_TO_TARGETS:
            with self.subTest(target=target):
                start_subworkflow.reset_mock()
                director = create_director(create_case(), {JUMP_TO_KEY: target})

                with self.captureOnCommitCallbacks(execute=True):
                    director.start()

                # Only the target subworkflow is started, with the one-off marker
                start_subworkflow.assert_called_once_with(
                    target, director.id, {JUMPED_TO_SUBWORKFLOW_KEY: True}
                )
                director.refresh_from_db()
                # Matched on message name: resume_after_debrief has a generated id
                self.assertIn(f"resume_after_{target}", waiting_messages(director))
                self.assertNotIn(JUMP_TO_KEY, director.data)

    def test_not_allowed_target_starts_director_normally(
        self, _, __, start_subworkflow
    ):
        director = create_director(create_case(), {JUMP_TO_KEY: "decision"})

        with self.assertLogs("apps.workflow.models", level="ERROR"):
            with self.captureOnCommitCallbacks(execute=True):
                director.start()

        # Normal start of the director: the first subworkflow is visit
        self.assertEqual(start_subworkflow.call_args.args[0], "visit")
        director.refresh_from_db()
        self.assertNotIn(JUMP_TO_KEY, director.data)

    def test_director_without_jump_to_starts_normally(self, _, __, start_subworkflow):
        director = create_director(create_case())

        with self.captureOnCommitCallbacks(execute=True):
            director.start()

        self.assertEqual(start_subworkflow.call_args.args[0], "visit")


@patch("apps.workflow.models.task_start_subworkflow.delay")
@patch("apps.workflow.models.task_complete_worflow.delay")
@patch("apps.workflow.signals.task_start_worflow.delay")
@patch("apps.workflow.tasks.task_create_main_worflow_for_case.delay")
class JumpedSubworkflowTest(TestCase):
    def setUp(self):
        management.call_command("flush", verbosity=0, interactive=False)
        super().setUp()

    def start_subworkflow(self, case, workflow_type, data):
        director = create_director(case)
        subworkflow = baker.make(
            CaseWorkflow,
            case=case,
            parent_workflow=director,
            workflow_type=workflow_type,
            data=data,
        )
        with self.captureOnCommitCallbacks(execute=True):
            subworkflow.start()
        subworkflow.refresh_from_db()
        return subworkflow

    def test_jumped_subworkflow_starts_at_first_task_with_event(self, *args):
        author = baker.make(get_user_model())
        for target, first_task in FIRST_TASKS.items():
            with self.subTest(target=target):
                case = create_case(author=author)
                subworkflow = self.start_subworkflow(
                    case, target, {JUMPED_TO_SUBWORKFLOW_KEY: True}
                )

                open_tasks = CaseUserTask.objects.filter(
                    workflow=subworkflow, completed=False
                )
                self.assertEqual(
                    list(open_tasks.values_list("task_name", flat=True)), [first_task]
                )
                # The subworkflow runs its own set_status scripts
                self.assertIsNotNone(subworkflow.case_state_type)
                self.assertNotIn(JUMPED_TO_SUBWORKFLOW_KEY, subworkflow.data)

                event = GenericCompletedTask.objects.get(
                    case=case, task_name=JUMP_EVENT_TASK_NAME
                )
                self.assertEqual(event.description, JUMP_EVENT_DESCRIPTION)
                self.assertEqual(event.author, author)
                self.assertEqual(
                    event.variables["mapped_form_data"][JUMP_TO_KEY]["value"],
                    open_tasks.get().name,
                )

    def test_no_event_without_jump_marker(self, *args):
        case = create_case(author=baker.make(get_user_model()))
        self.start_subworkflow(case, "summon", {})

        self.assertFalse(
            GenericCompletedTask.objects.filter(
                case=case, task_name=JUMP_EVENT_TASK_NAME
            ).exists()
        )

    def test_no_event_without_author(self, *args):
        case = create_case(author=None)
        with self.assertLogs("apps.workflow.models", level="WARNING"):
            self.start_subworkflow(case, "summon", {JUMPED_TO_SUBWORKFLOW_KEY: True})

        self.assertFalse(GenericCompletedTask.objects.filter(case=case).exists())
