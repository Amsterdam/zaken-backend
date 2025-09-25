from apps.workflow.spiff import compat as spiff_compat
from apps.workflow.utils import get_workflow_path, get_workflow_spec
from django.conf import settings
from django.test import SimpleTestCase


def _script_engine():
    """Return a script engine stub that exercises Spiff's hook points."""
    return spiff_compat.create_script_engine(
        scripting_additions={
            "set_status": lambda *args, **kwargs: None,
            "wait_for_workflows_and_send_message": lambda *args, **kwargs: None,
            "script_wait": lambda *args, **kwargs: None,
            "start_subworkflow": lambda *args, **kwargs: None,
            "parse_duration": lambda *args, **kwargs: None,
        }
    )


def _iter_workflow_versions():
    """Yield every (theme, workflow type, version) combination we ship."""
    for theme_name, types in settings.WORKFLOW_SPEC_CONFIG.items():
        for workflow_type, type_config in types.items():
            versions = (type_config or {}).get("versions", {})
            for version in versions.keys():
                yield theme_name, workflow_type, version


class WorkflowSmokeTests(SimpleTestCase):
    def test_all_bpmn_specs_parse(self):
        """Every configured BPMN model should still load and expose ready tasks."""
        for theme_name, workflow_type, version in _iter_workflow_versions():
            with self.subTest(
                theme=theme_name, workflow_type=workflow_type, version=version
            ):
                path = get_workflow_path(workflow_type, theme_name, version)
                spec = get_workflow_spec(path, workflow_type)
                self.assertIsNotNone(spec)

                workflow = spiff_compat.create_workflow(
                    spec, script_engine=_script_engine()
                )
                workflow.refresh_waiting_tasks()
                ready_tasks = workflow.get_tasks(spiff_compat.get_task_type().READY)

                # If the BPMN parsing or engine bootstrap breaks this will raise,
                # so just assert we end up with a list of ready tasks.
                self.assertIsInstance(ready_tasks, list)

    def test_workflow_serialization_roundtrip(self):
        """The serializer should round-trip without losing ready task context."""
        try:
            theme_name, workflow_type, version = next(_iter_workflow_versions())
        except StopIteration:  # pragma: no cover - safeguard if config is empty
            self.skipTest("No workflow versions configured")

        path = get_workflow_path(workflow_type, theme_name, version)
        spec = get_workflow_spec(path, workflow_type)

        script_engine = _script_engine()
        workflow = spiff_compat.create_workflow(spec, script_engine=script_engine)
        workflow.refresh_waiting_tasks()

        serialized = spiff_compat.serialize_workflow(workflow, include_spec=True)

        restored_workflow = spiff_compat.deserialize_workflow(serialized)
        restored_workflow.script_engine = _script_engine()
        restored_workflow.refresh_waiting_tasks()

        original_ready = [
            task.task_spec.name
            for task in workflow.get_tasks(spiff_compat.get_task_type().READY)
        ]
        restored_ready = [
            task.task_spec.name
            for task in restored_workflow.get_tasks(spiff_compat.get_task_type().READY)
        ]

        self.assertEqual(original_ready, restored_ready)
