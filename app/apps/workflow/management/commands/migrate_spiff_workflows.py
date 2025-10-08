import base64
import json
import pickle
import traceback

from apps.workflow.models import CaseWorkflow
from django.core.management.base import BaseCommand
from django.db import models, transaction
from SpiffWorkflow.bpmn.serializer import BpmnWorkflowSerializer
from SpiffWorkflow.bpmn.serializer.migration.version_migration import MIGRATIONS
from SpiffWorkflow.bpmn.serializer.workflow import VERSION as SPIFF_SERIALIZER_VERSION
from SpiffWorkflow.bpmn.workflow import BpmnWorkflow
from SpiffWorkflow.camunda.serializer.config import CAMUNDA_CONFIG


class Command(BaseCommand):
    help = "Migrates SpiffWorkflow v1 data to v3"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Runs the migration without saving any changes to the database.",
        )
        parser.add_argument(
            "--limit",
            type=int,
            help="Limits the number of workflows to process.",
        )
        parser.add_argument(
            "--workflow_id",
            type=int,
            help="Run the migration for a single, specific workflow.",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        self.stdout.write(
            self.style.SUCCESS("Starting SpiffWorkflow v1 to v3 migration...")
        )

        if dry_run:
            self.stdout.write(
                self.style.WARNING("Running in dry-run mode. No changes will be saved.")
            )

        workflows_to_migrate = self._get_workflows_to_migrate(options)
        self.stdout.write(f"Found {workflows_to_migrate.count()} workflows to migrate.")

        for workflow in workflows_to_migrate:
            self._process_workflow(workflow, dry_run)

        self.stdout.write(self.style.SUCCESS("Migration complete."))

    def _get_workflows_to_migrate(self, options):
        limit = options["limit"]
        workflow_id = options["workflow_id"]

        workflows = (
            CaseWorkflow.objects.filter(
                models.Q(spiff_workflow_version__isnull=True)
                | models.Q(spiff_workflow_version__startswith="1.")
            )
            .filter(spiff_serializer_version__isnull=True)
            .order_by("id")
        )

        if workflow_id:
            workflows = workflows.filter(id=workflow_id)
        if limit:
            workflows = workflows[:limit]
        return workflows

    def _process_workflow(self, workflow, dry_run):
        self.stdout.write(
            f"Processing workflow {workflow.id} for case {workflow.case.id}..."
        )
        try:
            self._transform_workflow_data(workflow)
            self._migrate_workflow_state(workflow)

            if not dry_run:
                with transaction.atomic():
                    workflow.save()

            self.stdout.write(
                self.style.SUCCESS(f"  - Successfully migrated workflow {workflow.id}")
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"  - Failed to migrate workflow {workflow.id}: {e}")
            )
            self.stdout.write(traceback.format_exc())

    def _transform_workflow_data(self, workflow):
        if not workflow.data:
            return

        # Keys that should NOT be wrapped in {"value": ...} structure
        # These should remain as raw values to match v3 format
        raw_value_keys = {
            "status_name",
            "monitoren_reactie_platform_duration",
            "result_var",
        }

        transformed_data = {}
        for key, value in workflow.data.items():
            # Skip obsolete fields that are no longer used in v3
            if key == "message_name":
                continue

            # For keys that should remain raw values
            if key in raw_value_keys:
                transformed_data[key] = value
            # For other keys, wrap in {"value": ...} if not already wrapped
            elif not isinstance(value, dict) or "value" not in value:
                transformed_data[key] = {"value": value}
            else:
                transformed_data[key] = value
        workflow.data = transformed_data

    def _migrate_workflow_state(self, workflow):
        state = self._prepare_initial_state(workflow)
        state = self._restructure_v0_state(state)
        state = self._ensure_spec_is_loaded(workflow, state)
        state = self._find_and_set_root_task(state)
        self._ensure_required_keys(state)

        # Transform task data in the serialized state to match v3 format BEFORE migrations
        state = self._transform_task_data_in_state(state)
        state = self._apply_migrations(state)

        # Add missing top-level keys for v3 compatibility
        state.setdefault("completed", False)
        state.setdefault("correlations", {})
        state.setdefault("bpmn_events", [])
        if "VERSION" in state:
            state["serializer_version"] = state.pop("VERSION")
        else:
            state["serializer_version"] = SPIFF_SERIALIZER_VERSION

        # Validate migration completed correctly
        self._validate_migration(state)

        # Use the same serialization pattern as the rest of the codebase
        # Create a workflow from the migrated state and serialize it properly
        workflow_spec = workflow.get_workflow_spec()
        if workflow_spec:
            # Create a dummy workflow to get proper serialization
            BpmnWorkflow(workflow_spec)
            serializer = BpmnWorkflowSerializer()
            reg = serializer.configure(CAMUNDA_CONFIG)
            serializer = BpmnWorkflowSerializer(registry=reg)

            # Deserialize the migrated state into a workflow object
            migrated_wf = serializer.deserialize_json(json.dumps(state))

            # Re-serialize using the proper serializer to ensure correct format
            workflow.serialized_workflow_state = serializer.serialize_json(migrated_wf)
            workflow.spiff_serializer_version = serializer.get_version(
                workflow.serialized_workflow_state
            )
        else:
            # Fallback to manual JSON serialization if no spec available
            workflow.serialized_workflow_state = json.dumps(state)
            workflow.spiff_serializer_version = SPIFF_SERIALIZER_VERSION

    def _prepare_initial_state(self, workflow):
        state = workflow.serialized_workflow_state
        if isinstance(state, str):
            state = json.loads(state)
        # V1 workflows are nested in a 'workflow' key.
        if "workflow" in state:
            state = state["workflow"]
        return state

    def _ensure_spec_is_loaded(self, workflow, state):
        if "spec" not in state or not state["spec"].get("task_specs"):
            workflow_spec = workflow.get_workflow_spec()
            if workflow_spec:
                dummy_wf = BpmnWorkflow(workflow_spec)
                serializer = BpmnWorkflowSerializer()
                reg = serializer.configure(CAMUNDA_CONFIG)
                serializer = BpmnWorkflowSerializer(registry=reg)
                serialized_dummy = serializer.serialize_json(dummy_wf)
                full_spec_state = json.loads(serialized_dummy)
                state["spec"] = full_spec_state["spec"]
        return state

    def _find_and_set_root_task(self, state):
        root_task_id = None
        if "tasks" in state and state["tasks"]:
            for task_id, task_data in state["tasks"].items():
                if isinstance(task_data, dict) and task_data.get("parent") is None:
                    root_task_id = task_id
                    break
        if root_task_id:
            state["root"] = root_task_id
        # Fallback for old states that still use 'start' in spec
        elif "spec" in state and "start" in state["spec"]:
            state["root"] = state["spec"].pop("start")
        return state

    def _ensure_required_keys(self, state):
        state.setdefault("subprocesses", {})
        state.setdefault("tasks", {})
        if "spec" not in state:
            state["spec"] = {}
        state["spec"].setdefault("task_specs", {})
        state.setdefault("subprocess_specs", {})

    def _restructure_v0_state(self, state):
        if "task_tree" not in state:
            return state

        if "last_task" in state and isinstance(state.get("last_task"), dict):
            state["last_task"] = state["last_task"].get("__uuid__")

        tasks = {}

        def _flatten_node(node):
            task_id = node.get("id", {}).get("__uuid__")
            if not task_id:
                return

            if isinstance(node.get("parent"), dict):
                node["parent"] = node["parent"].get("__uuid__")

            node["id"] = task_id

            children = node.pop("children", [])

            node["children"] = [
                child.get("id", {}).get("__uuid__")
                for child in children
                if child.get("id", {}).get("__uuid__")
            ]

            tasks[task_id] = node

            for child in children:
                _flatten_node(child)

        _flatten_node(state["task_tree"])
        state["tasks"] = tasks
        del state["task_tree"]

        return state

    def _transform_task_data_in_state(self, state):
        """Transform task data in the serialized workflow state to match v3 format."""
        # Also transform the top-level data dictionary, which was previously missed
        if "data" in state:
            state["data"] = self._transform_data_dict(state["data"])

        if "tasks" not in state:
            return state

        for task_id, task_data in state["tasks"].items():
            if "data" in task_data:
                task_data["data"] = self._transform_data_dict(task_data["data"])

            # Add typename field required for v3 format
            task_data.setdefault("typename", "Task")

        return state

    def _transform_data_dict(self, data_dict):
        """Transforms a v1 data dictionary to a v3 format by decoding __bytes__."""
        if not isinstance(data_dict, dict):
            return data_dict

        # Keys that should NOT be wrapped in {"value": ...} structure
        raw_value_keys = {
            "status_name",
            "monitoren_reactie_platform_duration",
            "result_var",
        }

        def decode_value(value):
            """Decode __bytes__ values from the old pickle format."""
            if isinstance(value, dict) and "__bytes__" in value:
                try:
                    # It's a pickled object that was base64 encoded
                    pickled_bytes = base64.b64decode(value["__bytes__"])
                    return pickle.loads(pickled_bytes)
                except Exception as e:
                    # Log the error and raise to ensure we catch decode failures
                    self.stdout.write(
                        self.style.WARNING(f"Failed to decode __bytes__ value: {e}")
                    )
                    raise
            return value

        transformed_data = {}
        for key, value in data_dict.items():
            # Skip obsolete fields that are no longer used in v3
            if key == "message_name":
                continue

            # First, decode the value if it's in the __bytes__ format
            decoded_value = decode_value(value)

            # The decoded value itself might be a dict with a 'value' key
            if isinstance(decoded_value, dict) and "value" in decoded_value:
                final_value = decoded_value["value"]
            else:
                final_value = decoded_value

            # Now, apply the wrapping logic
            if key in raw_value_keys:
                transformed_data[key] = final_value
            else:
                transformed_data[key] = {"value": final_value}
        return transformed_data

    def _apply_migrations(self, state):
        for _, migration_func in sorted(MIGRATIONS.items()):
            migration_func(state)
        return state

    def _validate_migration(self, state):
        """Validate that the migration completed correctly."""

        # Check that no __bytes__ fields remain
        def check_for_bytes(obj, path=""):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    if key == "__bytes__":
                        raise ValueError(
                            f"Found __bytes__ field at {path}.{key} - migration incomplete"
                        )
                    check_for_bytes(value, f"{path}.{key}" if path else key)
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    check_for_bytes(item, f"{path}[{i}]")

        check_for_bytes(state)

        # Check that all tasks have typename
        if "tasks" in state:
            for task_id, task_data in state["tasks"].items():
                if "typename" not in task_data:
                    raise ValueError(f"Task {task_id} missing typename field")

        # Check required v3 keys are present
        required_keys = ["completed", "correlations", "serializer_version"]
        for key in required_keys:
            if key not in state:
                raise ValueError(f"Missing required v3 key: {key}")
