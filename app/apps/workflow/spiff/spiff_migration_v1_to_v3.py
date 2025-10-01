"""
SpiffWorkflow v1 to v3 Data Migration Utility

This module provides utilities to migrate serialized workflow data from
SpiffWorkflow v1 format to v3 format.

Key changes:
- Tree structure → Flat dictionary
- Pickled data → Plain JSON
- Add missing v3 fields (typename, correlations, spec, etc.)
"""

import base64
import json
import logging
import pickle
from typing import Any, Dict, Optional, Tuple

logger = logging.getLogger(__name__)


# Mapping of task_spec patterns to typename
TASK_SPEC_TO_TYPENAME_MAP = {
    # Start events
    "Start": "Task",
    "StartEvent": "StartEvent",
    "start_": "StartEvent",
    # End events
    "End": "SimpleBpmnTask",
    "EndEvent": "EndEvent",
    "end_": "EndEvent",
    # Gateways
    "Gateway_": "Task",
    "gateway_": "Task",
    "ExclusiveGateway": "ExclusiveGateway",
    "ParallelGateway": "ParallelGateway",
    # Script tasks
    "script_": "ScriptTask",
    "service_": "ScriptTask",
    "ScriptTask": "ScriptTask",
    # User tasks
    "task_": "UserTask",
    "UserTask": "UserTask",
    # Message events
    "message_": "IntermediateCatchEvent",
    "resume_": "IntermediateCatchEvent",
    "Message": "IntermediateCatchEvent",
    # Special
    "Root": "Task",
    "StartEventSplit": "StartEventSplit",
    "StartEventJoin": "StartEventJoin",
    "EndJoin": "_EndJoin",
}


def unpickle_bytes(bytes_str: str) -> Any:
    """
    Decode __bytes__ pickled data to Python object

    Args:
        bytes_str: Base64 encoded pickled data

    Returns:
        Unpickled Python object or None if unpickling fails
    """
    try:
        decoded = base64.b64decode(bytes_str)
        return pickle.loads(decoded)
    except Exception as e:
        logger.warning(f"Failed to unpickle data: {e}")
        return None


def convert_data_field(data: Dict) -> Dict:
    """
    Convert v1 pickled data fields to v3 plain JSON

    In v1, some data fields were stored as:
    {"field_name": {"__bytes__": "base64_encoded_pickle_data"}}

    In v3, they should be plain JSON:
    {"field_name": actual_value}

    Args:
        data: Dictionary potentially containing __bytes__ fields

    Returns:
        Dictionary with unpickled values
    """
    result = {}
    for key, value in data.items():
        if isinstance(value, dict) and "__bytes__" in value:
            unpickled = unpickle_bytes(value["__bytes__"])
            # If unpickling fails, keep the original value
            result[key] = unpickled if unpickled is not None else value
        else:
            result[key] = value
    return result


def infer_typename(task_spec_name: str, task_data: Dict) -> str:
    """
    Infer the typename based on task_spec name and other characteristics

    Args:
        task_spec_name: Name of the task spec
        task_data: Task data containing state and other info

    Returns:
        Typename string (e.g., "Task", "ScriptTask", "UserTask")
    """
    if not task_spec_name:
        return "Task"

    # Check exact matches first
    if task_spec_name in TASK_SPEC_TO_TYPENAME_MAP:
        return TASK_SPEC_TO_TYPENAME_MAP[task_spec_name]

    # Check prefix matches
    for pattern, typename in TASK_SPEC_TO_TYPENAME_MAP.items():
        if task_spec_name.startswith(pattern):
            return typename

    # Check for specific patterns in the name
    spec_lower = task_spec_name.lower()

    if "gateway" in spec_lower:
        return "Task"  # Generic gateway
    if "script" in spec_lower or "service" in spec_lower:
        return "ScriptTask"
    if "message" in spec_lower or "resume" in spec_lower:
        return "IntermediateCatchEvent"
    if "event" in spec_lower:
        if "start" in spec_lower:
            return "StartEvent"
        elif "end" in spec_lower:
            return "EndEvent"
        else:
            return "IntermediateCatchEvent"
    # Only match "task" if it's likely a user task (starts with task_ or Activity_)
    if (
        spec_lower.startswith("task_") or spec_lower.startswith("activity_")
    ) and "gateway" not in spec_lower:
        return "UserTask"

    # Default to generic Task
    return "Task"


def convert_uuid_field(uuid_obj: Any) -> Optional[str]:
    """
    Convert v1 UUID format to v3 format

    v1: {"__uuid__": "abc-123-def"}
    v3: "abc-123-def"

    Args:
        uuid_obj: UUID object or dict with __uuid__ key

    Returns:
        UUID string or None
    """
    if uuid_obj is None:
        return None
    if isinstance(uuid_obj, dict) and "__uuid__" in uuid_obj:
        return uuid_obj["__uuid__"]
    if isinstance(uuid_obj, str):
        return uuid_obj
    return str(uuid_obj)


def tree_to_flat(task_tree: Dict, parent_id: Optional[str] = None) -> Dict[str, Dict]:
    """
    Convert v1 tree structure to v3 flat dictionary

    v1 stores tasks in a nested tree structure where each task has children.
    v3 stores all tasks in a flat dictionary with parent/child references.

    Args:
        task_tree: v1 task tree node
        parent_id: UUID of parent task (None for root)

    Returns:
        Dictionary mapping task UUIDs to task data
    """
    tasks = {}

    # Extract task ID
    task_id = convert_uuid_field(task_tree.get("id"))
    if not task_id:
        logger.error("Task has no ID, skipping")
        return tasks

    # Extract children IDs
    children_ids = [
        convert_uuid_field(child.get("id")) for child in task_tree.get("children", [])
    ]
    children_ids = [cid for cid in children_ids if cid]  # Filter out None values

    # Extract parent ID (if provided in old format)
    old_parent = convert_uuid_field(task_tree.get("parent"))
    actual_parent = old_parent if old_parent else parent_id

    # Infer typename
    task_spec_name = task_tree.get("task_spec", "")
    typename = infer_typename(task_spec_name, task_tree)

    # Build task entry
    task_entry = {
        "id": task_id,
        "parent": actual_parent,
        "children": children_ids,
        "last_state_change": task_tree.get("last_state_change"),
        "state": task_tree.get("state"),
        "task_spec": task_spec_name,
        "triggered": task_tree.get("triggered", False),
        "internal_data": task_tree.get("internal_data", {}),
        "data": convert_data_field(task_tree.get("data", {})),
        "typename": typename,
    }

    tasks[task_id] = task_entry

    # Recursively process children
    for child in task_tree.get("children", []):
        child_tasks = tree_to_flat(child, task_id)
        tasks.update(child_tasks)

    return tasks


def detect_format_version(data: str) -> str:
    """
    Detect if serialized data is v1 or v3 format

    Args:
        data: JSON string of serialized workflow

    Returns:
        "v1", "v3", or "unknown"
    """
    try:
        obj = json.loads(data) if isinstance(data, str) else data

        # v1 has task_tree, v3 has tasks dict
        if "task_tree" in obj and "tasks" not in obj:
            return "v1"
        elif "tasks" in obj and isinstance(obj["tasks"], dict):
            return "v3"
        else:
            return "unknown"
    except Exception as e:
        logger.error(f"Error detecting format: {e}")
        return "unknown"


def validate_v3_structure(v3_obj: Dict) -> Tuple[bool, list]:
    """
    Validate that v3 object has required fields and structure

    Args:
        v3_obj: Converted v3 workflow object

    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []
    required_fields = [
        "data",
        "correlations",
        "last_task",
        "success",
        "completed",
        "tasks",
        "root",
        "subprocess_specs",
        "subprocesses",
        "bpmn_events",
        "typename",
        "serializer_version",
    ]

    for field in required_fields:
        if field not in v3_obj:
            errors.append(f"Missing required field: {field}")

    # Validate tasks structure
    if "tasks" in v3_obj:
        if not isinstance(v3_obj["tasks"], dict):
            errors.append("tasks must be a dictionary")
        else:
            for task_id, task_data in v3_obj["tasks"].items():
                if "typename" not in task_data:
                    errors.append(f"Task {task_id} missing typename")
                if "id" not in task_data:
                    errors.append(f"Task {task_id} missing id field")

    # Validate root exists in tasks
    if "root" in v3_obj and "tasks" in v3_obj:
        if v3_obj["root"] not in v3_obj["tasks"]:
            errors.append(f"Root task {v3_obj['root']} not found in tasks")

    # Validate last_task exists in tasks
    if "last_task" in v3_obj and v3_obj["last_task"] and "tasks" in v3_obj:
        if v3_obj["last_task"] not in v3_obj["tasks"]:
            errors.append(f"Last task {v3_obj['last_task']} not found in tasks")

    return len(errors) == 0, errors


def migrate_v1_to_v3(v1_data: str, workflow_spec=None) -> str:
    """
    Main migration function: Convert v1 serialized data to v3 format

    Args:
        v1_data: JSON string of v1 serialized workflow
        workflow_spec: BpmnProcessSpec object for the workflow (optional, used for spec injection)

    Returns:
        JSON string of v3 serialized workflow

    Raises:
        ValueError: If data is not in v1 format or migration fails
    """
    # Parse v1 data
    try:
        v1_obj = json.loads(v1_data) if isinstance(v1_data, str) else v1_data
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON: {e}")

    # Verify it's v1 format
    if detect_format_version(v1_obj) != "v1":
        raise ValueError("Data is not in v1 format")

    # Convert tree to flat structure
    task_tree = v1_obj.get("task_tree", {})
    if not task_tree:
        raise ValueError("No task_tree found in v1 data")

    tasks = tree_to_flat(task_tree)

    # Extract root task ID
    root_id = convert_uuid_field(task_tree.get("id"))
    if not root_id:
        raise ValueError("Could not determine root task ID")

    # Extract last_task ID
    last_task_obj = v1_obj.get("last_task")
    last_task_id = convert_uuid_field(last_task_obj)

    # Convert top-level data
    top_level_data = convert_data_field(v1_obj.get("data", {}))

    # Build v3 structure
    v3_obj = {
        "data": top_level_data,
        "correlations": {},
        "last_task": last_task_id,
        "success": v1_obj.get("success", True),
        "completed": False,  # Will be determined by workflow state
        "tasks": tasks,
        "root": root_id,
        "spec": None,  # Spec will be populated during deserialization
        "subprocess_specs": {},
        "subprocesses": {},
        "bpmn_events": [],
        "typename": "BpmnWorkflow",
        "serializer_version": "1.4",
    }

    # Validate structure
    is_valid, errors = validate_v3_structure(v3_obj)
    if not is_valid:
        raise ValueError(f"Migration produced invalid v3 structure: {errors}")

    return json.dumps(v3_obj)


def is_v1_format(serialized_state: Any) -> bool:
    """
    Check if serialized workflow state is in v1 format

    Args:
        serialized_state: Workflow state (string or dict)

    Returns:
        True if v1 format, False otherwise
    """
    try:
        if isinstance(serialized_state, str):
            obj = json.loads(serialized_state)
        else:
            obj = serialized_state

        return detect_format_version(obj) == "v1"
    except Exception:
        return False


def get_migration_stats(v1_data: str, v3_data: str) -> Dict[str, Any]:
    """
    Generate statistics about the migration

    Args:
        v1_data: Original v1 JSON string
        v3_data: Migrated v3 JSON string

    Returns:
        Dictionary with migration statistics
    """
    v1_obj = json.loads(v1_data) if isinstance(v1_data, str) else v1_data
    v3_obj = json.loads(v3_data) if isinstance(v3_data, str) else v3_data

    # Count tasks in v1 (recursive)
    def count_tasks_v1(tree):
        count = 1
        for child in tree.get("children", []):
            count += count_tasks_v1(child)
        return count

    v1_task_count = count_tasks_v1(v1_obj.get("task_tree", {}))
    v3_task_count = len(v3_obj.get("tasks", {}))

    # Count data fields that were unpickled
    def count_unpickled_fields(data):
        count = 0
        for value in data.values():
            if isinstance(value, dict) and "__bytes__" in value:
                count += 1
        return count

    v1_pickled_count = count_unpickled_fields(v1_obj.get("data", {}))

    # Get task type distribution
    task_types = {}
    for task in v3_obj.get("tasks", {}).values():
        typename = task.get("typename", "Unknown")
        task_types[typename] = task_types.get(typename, 0) + 1

    return {
        "v1_task_count": v1_task_count,
        "v3_task_count": v3_task_count,
        "task_count_match": v1_task_count == v3_task_count,
        "unpickled_fields": v1_pickled_count,
        "task_type_distribution": task_types,
        "root_task": v3_obj.get("root"),
        "last_task": v3_obj.get("last_task"),
    }
