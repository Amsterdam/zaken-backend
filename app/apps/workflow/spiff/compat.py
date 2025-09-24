"""Compatibility layer for SpiffWorkflow access.

This isolates all direct Spiff imports so we can swap implementations when
upgrading to newer versions. Callers should only use the helpers defined
here instead of importing Spiff modules directly.
"""

from __future__ import annotations

from typing import Any, Dict, Iterable, Optional

from SpiffWorkflow.bpmn.PythonScriptEngine import PythonScriptEngine
from SpiffWorkflow.bpmn.serializer.BpmnSerializer import BpmnSerializer
from SpiffWorkflow.bpmn.specs.BpmnProcessSpec import BpmnProcessSpec
from SpiffWorkflow.bpmn.workflow import BpmnWorkflow
from SpiffWorkflow.camunda.parser.CamundaParser import CamundaParser
from SpiffWorkflow.camunda.specs.UserTask import UserTask
from SpiffWorkflow.specs.StartTask import StartTask
from SpiffWorkflow.task import Task

# Public re-exports for callers that need to type-check against task specs.
BoundaryEventSpec = None


def _load_boundary_event_spec():
    """Load the BoundaryEventSpec class."""

    from SpiffWorkflow.bpmn.specs.BoundaryEvent import BoundaryEvent

    return BoundaryEvent


def load_spec(path: str, workflow_type: str):
    """Load a BPMN spec from the given path using the Camunda parser."""

    parser = CamundaParser()
    for file_path in iter_bpmn_files(path):
        parser.add_bpmn_file(file_path)
    return parser.get_spec(workflow_type)


def get_boundary_event_type():
    """Return the BoundaryEventSpec class."""

    global BoundaryEventSpec
    if BoundaryEventSpec is None:
        BoundaryEventSpec = _load_boundary_event_spec()
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

    return PythonScriptEngine(scriptingAdditions=scripting_additions or {})


def create_workflow(spec, script_engine=None):
    """Instantiate a BpmnWorkflow with the given spec and script engine."""

    return BpmnWorkflow(spec, script_engine=script_engine)


def serialize_workflow(workflow, include_spec: bool = False):
    """Serialize a workflow instance to JSON."""

    serializer = BpmnSerializer()
    return serializer.serialize_workflow(workflow, include_spec=include_spec)


def deserialize_workflow(state, workflow_spec=None):
    """Deserialize a workflow instance from JSON."""

    serializer = BpmnSerializer()
    return serializer.deserialize_workflow(state, workflow_spec=workflow_spec)


def get_task_type():
    """Return the Task class."""

    return Task


def get_user_task_type():
    """Return the UserTask class."""

    return UserTask


def get_start_task_type():
    """Return the StartTask class."""

    return StartTask


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
]
