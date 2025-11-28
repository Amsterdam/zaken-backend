from __future__ import annotations

from typing import Any, Iterable, List

from django import template
from SpiffWorkflow.util.task import TaskState

register = template.Library()


@register.filter(name="task_state_name")
def task_state_name(task: Any) -> str:
    """Return a human friendly state name for a Spiff task."""

    if TaskState is None or task is None:
        return "UNKNOWN"

    state_value = None
    if hasattr(task, "get_state") and callable(task.get_state):
        state_value = task.get_state()
    elif hasattr(task, "state"):
        state_value = task.state

    if state_value is None:
        return "UNKNOWN"

    try:
        return TaskState.get_name(state_value) or f"UNKNOWN({state_value})"
    except (
        Exception
    ):  # pragma: no cover - defensive, TaskState.get_name should not raise
        return f"UNKNOWN({state_value})"


@register.filter(name="task_display_name")
def task_display_name(task: Any) -> str:
    """Return a readable task display name."""

    if task is None:
        return "Task"

    # Spiff v3 Task exposes .task_spec with various metadata
    task_spec = getattr(task, "task_spec", None)
    name_candidates: Iterable[str] = []
    if task_spec is not None:
        name_candidates = (
            getattr(task_spec, "description", ""),
            getattr(task_spec, "bpmn_name", ""),
            getattr(task_spec, "name", ""),
            getattr(task_spec.__class__, "__name__", ""),
        )
    else:
        name_candidates = (getattr(task, "name", ""),)

    for candidate in name_candidates:
        if isinstance(candidate, str) and candidate.strip():
            return candidate

    task_id = getattr(task, "id", None)
    return f"Task {task_id}" if task_id else "Task"


@register.filter(name="task_spec_name")
def task_spec_name(task: Any) -> str:
    """Return the technical BPMN spec name for the task."""

    if task is None:
        return ""

    task_spec = getattr(task, "task_spec", None)
    candidates: Iterable[str] = (
        getattr(task_spec, "name", "") if task_spec else "",
        getattr(task_spec, "bpmn_name", "") if task_spec else "",
        getattr(task, "name", ""),
    )

    for candidate in candidates:
        if isinstance(candidate, str) and candidate.strip():
            return candidate

    task_id = getattr(task, "id", None)
    return str(task_id) if task_id else ""


def _build_children(task: Any) -> List[Any]:
    if task is None:
        return []

    # Spiff v3 Task.children returns list[Task]
    children = getattr(task, "children", None)
    if callable(children):
        return list(children())
    if isinstance(children, list):
        return children

    return []


@register.simple_tag(name="task_children")
def task_children(task: Any) -> List[Any]:
    return _build_children(task)
