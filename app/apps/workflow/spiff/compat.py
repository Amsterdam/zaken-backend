"""Compatibility layer for SpiffWorkflow access.

This isolates all direct Spiff imports so we can swap implementations when
upgrading to newer versions. Callers should only use the helpers defined
here instead of importing Spiff modules directly.
"""

from __future__ import annotations

from typing import Any, Dict, Iterable, Optional

from SpiffWorkflow.bpmn.script_engine import PythonScriptEngine, TaskDataEnvironment
from SpiffWorkflow.bpmn.serializer import BpmnWorkflowSerializer
from SpiffWorkflow.bpmn.specs.bpmn_process_spec import BpmnProcessSpec
from SpiffWorkflow.bpmn.specs.defaults import BoundaryEvent
from SpiffWorkflow.bpmn.util.event import BpmnEvent
from SpiffWorkflow.bpmn.workflow import BpmnWorkflow
from SpiffWorkflow.camunda.parser.CamundaParser import CamundaParser
from SpiffWorkflow.camunda.serializer.config import CAMUNDA_CONFIG
from SpiffWorkflow.camunda.specs.user_task import UserTask

# Public re-exports for callers that need to type-check against task specs.
BoundaryEventSpec = BoundaryEvent


def _load_boundary_event_spec():
    """Retained for backwards compatibility with legacy import paths."""

    return BoundaryEvent


def load_spec(path: str, workflow_type: str):
    """Load a BPMN spec from the given path using the Camunda parser."""

    parser = CamundaParser()
    for file_path in iter_bpmn_files(path):
        parser.add_bpmn_file(file_path)
    return parser.get_spec(workflow_type)


def get_boundary_event_type():
    """Return the BoundaryEventSpec class."""

    return BoundaryEventSpec


def iter_bpmn_files(path: str) -> Iterable[str]:
    """Iterate over all BPMN files in the given path."""

    import os

    for file_name in os.listdir(path):
        full_path = os.path.join(path, file_name)
        if os.path.isfile(full_path) and file_name.endswith(".bpmn"):
            yield full_path


def create_script_engine(scripting_additions: Optional[Dict[str, Any]] = None):
    """Return a PythonScriptEngine with our custom scripting additions."""

    environment = TaskDataEnvironment(environment_globals=scripting_additions or {})
    return PythonScriptEngine(environment=environment)


def create_workflow(spec, script_engine=None):
    """Instantiate a BpmnWorkflow with the given spec and script engine."""

    return BpmnWorkflow(spec, script_engine=script_engine)


def serialize_workflow(workflow, include_spec: bool = False):
    """Serialize a workflow instance to JSON."""

    registry = BpmnWorkflowSerializer.configure(CAMUNDA_CONFIG)
    serializer = BpmnWorkflowSerializer(registry=registry)
    return serializer.serialize_json(workflow)


def deserialize_workflow(state, workflow_spec=None):
    """Deserialize a workflow instance from JSON."""

    registry = BpmnWorkflowSerializer.configure(CAMUNDA_CONFIG)
    serializer = BpmnWorkflowSerializer(registry=registry)
    workflow = serializer.deserialize_json(state)

    if workflow_spec is not None:
        workflow.spec = workflow_spec

    return workflow


def get_task_type():
    """Return the Task class."""

    from SpiffWorkflow import TaskState

    return TaskState


def get_user_task_type():
    """Return the UserTask class."""

    return UserTask


def update_task_data(task, data):
    """Mirror the old Task.update_data helper from Spiff v1."""

    if not data:
        return task

    if isinstance(getattr(task, "data", None), dict):
        task.data.update(_with_attr_access(data))

    workflow = getattr(task, "workflow", None)
    if workflow and isinstance(getattr(workflow, "data", None), dict):
        workflow.data.update(_with_attr_access(data))

    return task


def accept_message(workflow, message_name, data=None, correlation_key=None):
    """Replaces the old Workflow.message helper from Spiff v1."""

    payload_data = data if isinstance(data, dict) else {"value": data}
    payload_data = _with_attr_access(payload_data)
    event_payload = DotDict(
        {
            "payload": payload_data,
            "result_var": f"{message_name}_payload",
        }
    )
    event = BpmnEvent(
        event_definition=_get_message_event_definition(workflow, message_name),
        payload=event_payload,
        correlations={},
    )
    workflow.send_event(event)


def _get_message_event_definition(workflow, message_name):
    for spec in workflow.spec.task_specs.values():
        event_def = getattr(spec, "event_definition", None)
        if event_def and getattr(event_def, "name", None) == message_name:
            return event_def
    raise RuntimeError(
        f"Message '{message_name}' not found in workflow spec '{workflow.spec.name}'"
    )


def _with_attr_access(value):
    if isinstance(value, dict):
        return DotDict({k: _with_attr_access(v) for k, v in value.items()})
    if isinstance(value, list):
        return [_with_attr_access(v) for v in value]
    return value


class DotDict(dict):
    """Dict that also exposes keys as attributes."""

    def __getattr__(self, item):
        try:
            return self[item]
        except KeyError as exc:
            raise AttributeError(item) from exc

    def __setattr__(self, key, value):
        self[key] = value


def get_start_task_type():
    """Return the StartTask class."""

    from SpiffWorkflow.camunda.parser.CamundaParser import CamundaParser

    return CamundaParser.OVERRIDE_PARSER_CLASSES[
        "{http://www.omg.org/spec/BPMN/20100524/MODEL}startEvent"
    ][1]


def get_bpmn_process_spec_type():
    """Return the BpmnProcessSpec class."""

    return BpmnProcessSpec


__all__ = [
    "create_script_engine",
    "load_spec",
    "iter_bpmn_files",
    "create_workflow",
    "serialize_workflow",
    "deserialize_workflow",
    "get_task_type",
    "get_user_task_type",
    "get_start_task_type",
    "get_boundary_event_type",
    "update_task_data",
    "accept_message",
]
