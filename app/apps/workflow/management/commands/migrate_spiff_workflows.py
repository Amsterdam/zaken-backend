import base64
import json
import pickle
import traceback
from io import BytesIO

from apps.workflow.models import CaseWorkflow
from django.core.management.base import BaseCommand
from django.db import models, transaction
from SpiffWorkflow.bpmn.serializer import BpmnWorkflowSerializer
from SpiffWorkflow.bpmn.serializer.migration.version_migration import MIGRATIONS
from SpiffWorkflow.bpmn.serializer.workflow import VERSION as SPIFF_SERIALIZER_VERSION
from SpiffWorkflow.bpmn.workflow import BpmnWorkflow
from SpiffWorkflow.camunda.serializer.config import CAMUNDA_CONFIG


class PythonScriptEngine:
    """
    A placeholder for the old PythonScriptEngine class that behaves like a dictionary.

    See: https://github.com/sartography/SpiffWorkflow/blob/v2.0.1/RELEASE_NOTES.md#flexible-data-management
    """


class Box(dict):
    """
    A placeholder for the old Box class that behaves like a dictionary
    to support unpickling, while also providing a `value` property for
    compatibility with the migration logic.

    See: https://github.com/sartography/SpiffWorkflow/blob/v3.1.2/RELEASE_NOTES.md#other-changes
    """

    @property
    def value(self):
        return self.get("value")

    @value.setter
    def value(self, val):
        self["value"] = val


class CustomUnpickler(pickle.Unpickler):
    """
    A custom unpickler to handle obsolete classes from SpiffWorkflow v1.
    """

    def find_class(self, module, name):
        if module == "SpiffWorkflow.bpmn.PythonScriptEngine":
            if name == "PythonScriptEngine":
                return PythonScriptEngine
            if name == "Box":
                return Box
        return super().find_class(module, name)


def decode_value(value):
    """Decode __bytes__ values from the old pickle format using a custom unpickler."""
    if isinstance(value, dict) and "__bytes__" in value:
        try:
            pickled_bytes = base64.b64decode(value["__bytes__"])
            return CustomUnpickler(BytesIO(pickled_bytes)).load()
        except Exception:
            # Re-raise the exception to be caught and logged by the command
            raise
    return value


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

        success_count = 0
        error_count = 0

        for workflow in workflows_to_migrate:
            success = self._process_workflow(workflow, dry_run)
            if success:
                success_count += 1
            else:
                error_count += 1

        self.stdout.write(self.style.SUCCESS("\nMigration complete."))
        self.stdout.write(f"Successfully migrated: {success_count} workflows")
        if error_count > 0:
            self.stdout.write(
                self.style.ERROR(f"Failed to migrate: {error_count} workflows")
            )

    def _get_workflows_to_migrate(self, options):
        """
        Retrieves the workflows that need to be migrated from the database.
        It filters for workflows that have a spiff_workflow_version of 1 or None,
        and no spiff_serializer_version. It also applies optional limits and
        workflow_id filters.
        """
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
        """
        Processes a single workflow, handling the migration of its data and state.
        It backs up the original data and serialized state before attempting
        the migration. If the migration is successful and not in dry-run mode,
        it saves the changes to the database.

        Returns True if successful, False otherwise.
        """
        workflow_type = workflow.workflow_type or "unknown"
        self.stdout.write(
            f"\nProcessing workflow {workflow.id} ({workflow_type}) for case {workflow.case.id}..."
        )
        try:
            workflow.data_migration_backup = workflow.data
            workflow.serialized_workflow_state_migration_backup = (
                workflow.serialized_workflow_state
            )
            self._transform_workflow_data(workflow)
            self._migrate_workflow_state(workflow)

            if not dry_run:
                with transaction.atomic():
                    workflow.save()

            self.stdout.write(
                self.style.SUCCESS(f"  ✅ Successfully migrated workflow {workflow.id}")
            )
            return True
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"  ❌ Failed to migrate workflow {workflow.id}: {e}")
            )
            self.stdout.write(traceback.format_exc())
            return False

    def _transform_data(
        self,
        data_dict,
        value_processor=None,
        wrap_conditionally=False,
        wrap_values=True,
    ):
        """
        Generic helper to transform a v1 data dictionary to a v3 format.

        :param data_dict: The dictionary to transform.
        :param value_processor: A function to process/decode values before transformation.
        :param wrap_conditionally: If True, wraps values only if not already wrapped.
        :param wrap_values: If False, no values are wrapped.
        """
        if not isinstance(data_dict, dict):
            return data_dict

        # Keys that should not be wrapped in {"value": ...} structure.
        # Note we're doing this for any `_duration` keys later on.
        raw_value_keys = {
            "completed",
            "result_var",
            "status_name",
        }

        transformed_data = {}
        for key, value in data_dict.items():
            if key == "message_name":
                continue

            processed_value = value_processor(value) if value_processor else value

            if not wrap_values:
                transformed_data[key] = processed_value
                continue

            if key in raw_value_keys or key.endswith("_duration"):
                transformed_data[key] = processed_value
            elif wrap_conditionally and (isinstance(value, dict) and "value" in value):
                transformed_data[key] = value
            else:
                transformed_data[key] = {"value": processed_value}
        return transformed_data

    def _process_and_decode_value(self, value):
        """
        Decodes and unwraps a value from a v1 data dictionary. It handles
        the custom __bytes__ format, unwraps values from dictionaries
        containing a 'value' key, and handles the old Box class.
        """
        decoded_value = decode_value(value)

        if isinstance(decoded_value, dict) and "value" in decoded_value:
            return decoded_value["value"]
        if isinstance(decoded_value, Box):
            return decoded_value.value
        return decoded_value

    def _transform_workflow_data(self, workflow):
        """
        Transforms the top-level data dictionary of a workflow to the v3 format.
        It uses a conditional wrap to ensure that values are not double-wrapped.
        """
        if not workflow.data:
            return

        workflow.data = self._transform_data(workflow.data, wrap_conditionally=True)

    def _migrate_workflow_state(self, workflow):
        """
        Orchestrates the migration of the serialized workflow state from v1 to v3.
        This involves preparing the initial state, restructuring it, ensuring the
        spec is loaded, setting the root task, transforming task data, applying
        migrations, setting display names, and finally re-serializing the state
        in the v3 format.
        """
        state = self._prepare_initial_state(workflow)
        state = self._restructure_v1_state(state)
        state = self._ensure_spec_is_loaded(workflow, state)
        state = self._find_and_set_root_task(state)
        self._ensure_required_keys(state)

        # Transform task data in the serialized state to match v3 format BEFORE migrations
        state = self._transform_task_data_in_state(state)
        state = self._apply_migrations(state)

        # Set display names from BPMN spec before further processing
        state = self._set_display_names_from_spec(workflow, state)

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
        """
        Prepares the initial state for migration. It loads the serialized state
        from the workflow, handling both string and dictionary formats, and
        unwraps the v1 state from the 'workflow' key if present.
        """
        state = workflow.serialized_workflow_state
        if isinstance(state, str):
            state = json.loads(state)
        # V1 workflows are nested in a 'workflow' key.
        if "workflow" in state:
            state = state["workflow"]
        return state

    def _ensure_spec_is_loaded(self, workflow, state):
        """
        Ensures that the workflow specification is loaded into the state.
        If the spec or its task_specs are missing, it loads them from the
        workflow's BPMN definition by creating a dummy workflow and
        serializing it to extract the spec.
        """
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
        """
        Finds and sets the root task in the workflow state. It iterates over
        the tasks to find the one with no parent and sets it as the root.
        It also includes a fallback for older states that use a 'start'
        key in the spec.
        """
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
        """
        Ensures that all required keys for the v3 format are present in the
        workflow state, adding them with default values if they are missing.
        """
        state.setdefault("subprocesses", {})
        state.setdefault("tasks", {})
        if "spec" not in state:
            state["spec"] = {}
        state["spec"].setdefault("task_specs", {})
        state.setdefault("subprocess_specs", {})

    def _restructure_v1_state(self, state):
        """
        Restructures the v1 task_tree into the flat 'tasks' dictionary format
        used in v3. It recursively flattens the tree structure and updates
        parent/child references to use UUIDs.
        """
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

    def _set_display_names_from_spec(self, workflow, state):
        """
        Set display_name for task specs from the BPMN workflow specification.
        This ensures that user tasks have proper human-readable names after migration.
        """
        workflow_spec = workflow.get_workflow_spec()
        if not workflow_spec:
            self.stdout.write(
                self.style.WARNING(
                    f"  - No workflow spec found for workflow {workflow.id}"
                )
            )
            return state

        if "spec" not in state or "task_specs" not in state["spec"]:
            self.stdout.write(
                self.style.WARNING(
                    f"  - No spec or task_specs found for workflow {workflow.id}"
                )
            )
            return state

        for task_spec_name, task_spec_data in state["spec"]["task_specs"].items():
            try:
                # Find the corresponding task in the parsed BPMN workflow spec
                bpmn_task = workflow_spec.get_task_spec_from_name(task_spec_name)

                if (
                    bpmn_task
                    and hasattr(bpmn_task, "bpmn_name")
                    and bpmn_task.bpmn_name
                ):
                    # Set the `bpmn_name` and `description` fields to the spec data
                    display_name = bpmn_task.bpmn_name
                    task_spec_data["description"] = display_name
                    task_spec_data["bpmn_name"] = display_name
            except Exception as e:
                # Log warning but don't fail the migration
                self.stdout.write(
                    self.style.WARNING(
                        f"  - Could not set bpmn_name and description for {task_spec_name}: {e}"
                    )
                )

        return state

    def _transform_task_data_in_state(self, state):
        """
        Transform task data in the serialized workflow state to match v3 format.
        It processes the data dictionaries for the top-level state and for each
        individual task, and ensures that each task has a 'typename' field.
        """
        # Also transform the top-level data dictionary, which was previously missed
        if "data" in state:
            state["data"] = self._transform_data_dict(state["data"])

        if "internal_data" in state:
            state["internal_data"] = self._transform_internal_data(
                state["internal_data"]
            )

        if "tasks" not in state:
            return state

        for task_id, task_data in state["tasks"].items():
            if "data" in task_data:
                task_data["data"] = self._transform_data_dict(task_data["data"])

            if "internal_data" in task_data:
                task_data["internal_data"] = self._transform_internal_data(
                    task_data["internal_data"]
                )

            # Add typename field required for v3 format
            task_data.setdefault("typename", "Task")

        return state

    def _transform_data_dict(self, data_dict, wrap_values=True):
        """
        Transforms a v1 data dictionary to a v3 format by decoding __bytes__.
        This is a helper function that calls the more generic _transform_data
        with a specific value processor for decoding.
        """
        return self._transform_data(
            data_dict,
            value_processor=self._process_and_decode_value,
            wrap_values=wrap_values,
        )

    def _transform_internal_data(self, internal_data):
        """
        Converts legacy internal_data keys to their v3 equivalents.

        Specifically, any key from the `key_mapping` dictionary is renamed to the value
        of the key in the dictionary unless the latter already exists. The transformation
        is applied recursively to nested structures to ensure consistency throughout
        the payload.
        """

        key_mapping = {
            "start_time": "event_value",
        }

        if isinstance(internal_data, dict):
            transformed = {}
            for key, value in internal_data.items():
                processed_value = self._transform_internal_data(value)

                if key in key_mapping:
                    mapped_key = key_mapping[key]
                    if mapped_key in internal_data:
                        continue
                    transformed_key = mapped_key
                else:
                    transformed_key = key

                transformed[transformed_key] = processed_value

            return transformed

        if isinstance(internal_data, list):
            return [self._transform_internal_data(item) for item in internal_data]

        return internal_data

    def _apply_migrations(self, state):
        """
        Applies the SpiffWorkflow migrations to the workflow state. It iterates
        over the registered migrations in order and applies each one.
        """
        for _, migration_func in sorted(MIGRATIONS.items()):
            migration_func(state)
        return state

    def _validate_migration(self, state):
        """
        Validate that the migration completed correctly. This includes checking
        that no __bytes__ fields remain, that all tasks have a 'typename',
        and that all required v3 top-level keys are present.
        """

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
