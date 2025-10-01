"""
Unit tests for SpiffWorkflow v1 to v3 migration

Tests cover:
- Data format detection
- Tree to flat conversion
- Pickle data unpacking
- Typename inference
- Full migration workflow
- Validation
"""

import base64
import json
import pickle

from apps.cases.models import Case, CaseTheme
from apps.workflow.models import CaseWorkflow
from apps.workflow.spiff.spiff_migration_v1_to_v3 import (
    convert_data_field,
    convert_uuid_field,
    detect_format_version,
    get_migration_stats,
    infer_typename,
    is_v1_format,
    migrate_v1_to_v3,
    tree_to_flat,
    unpickle_bytes,
    validate_v3_structure,
)
from django.conf import settings
from django.test import TestCase
from model_bakery import baker


class UnpickleDataTests(TestCase):
    """Test unpickling of v1 data fields"""

    def test_unpickle_bytes_success(self):
        """Test successful unpickling of bytes data"""
        # Create a pickled value
        original_value = {"value": "test_value"}
        pickled = pickle.dumps(original_value)
        encoded = base64.b64encode(pickled).decode("utf-8")

        result = unpickle_bytes(encoded)
        self.assertEqual(result, original_value)

    def test_unpickle_bytes_invalid(self):
        """Test unpickling with invalid data returns None"""
        result = unpickle_bytes("invalid_base64_data")
        self.assertIsNone(result)

    def test_convert_data_field_with_bytes(self):
        """Test converting data field with __bytes__ entries"""
        original_value = {"value": "No"}
        pickled = pickle.dumps(original_value)
        encoded = base64.b64encode(pickled).decode("utf-8")

        data = {
            "authorization": {"__bytes__": encoded},
            "status_name": "Huisbezoek",
            "theme": {"value": "theme_kamerverhuur"},
        }

        result = convert_data_field(data)

        self.assertEqual(result["authorization"], original_value)
        self.assertEqual(result["status_name"], "Huisbezoek")
        self.assertEqual(result["theme"], {"value": "theme_kamerverhuur"})

    def test_convert_data_field_without_bytes(self):
        """Test converting data field without __bytes__ entries"""
        data = {"status_name": "Huisbezoek", "theme": {"value": "theme_kamerverhuur"}}

        result = convert_data_field(data)
        self.assertEqual(result, data)


class TypenameInferenceTests(TestCase):
    """Test typename inference logic"""

    def test_infer_typename_script_task(self):
        """Test inference for script tasks"""
        self.assertEqual(
            infer_typename("script_start_visit_subworkflow", {}), "ScriptTask"
        )
        self.assertEqual(
            infer_typename("service_script_set_super_process", {}), "ScriptTask"
        )

    def test_infer_typename_user_task(self):
        """Test inference for user tasks"""
        self.assertEqual(infer_typename("task_create_concept_summons", {}), "UserTask")

    def test_infer_typename_gateway(self):
        """Test inference for gateways"""
        self.assertEqual(infer_typename("Gateway_1ghwpqi", {}), "Task")
        self.assertEqual(infer_typename("gateway_merge_1obmbig", {}), "Task")

    def test_infer_typename_message_event(self):
        """Test inference for message events"""
        self.assertEqual(
            infer_typename("resume_after_visit", {}), "IntermediateCatchEvent"
        )
        self.assertEqual(
            infer_typename("message_wait_for_summons", {}), "IntermediateCatchEvent"
        )

    def test_infer_typename_start_event(self):
        """Test inference for start events"""
        self.assertEqual(infer_typename("Start", {}), "Task")
        self.assertEqual(
            infer_typename("start_aanschrijving_toevoegen", {}), "StartEvent"
        )

    def test_infer_typename_end_event(self):
        """Test inference for end events"""
        self.assertEqual(infer_typename("End", {}), "SimpleBpmnTask")
        self.assertEqual(infer_typename("end_0ins2a3", {}), "EndEvent")

    def test_infer_typename_special_tasks(self):
        """Test inference for special task types"""
        self.assertEqual(infer_typename("Root", {}), "Task")
        self.assertEqual(infer_typename("StartEventSplit", {}), "StartEventSplit")
        self.assertEqual(infer_typename("StartEventJoin", {}), "StartEventJoin")

    def test_infer_typename_default(self):
        """Test default typename for unknown patterns"""
        self.assertEqual(infer_typename("unknown_task_name", {}), "Task")


class UUIDConversionTests(TestCase):
    """Test UUID format conversion"""

    def test_convert_uuid_dict(self):
        """Test conversion from dict format"""
        uuid_dict = {"__uuid__": "abc-123-def"}
        result = convert_uuid_field(uuid_dict)
        self.assertEqual(result, "abc-123-def")

    def test_convert_uuid_string(self):
        """Test conversion from string format"""
        result = convert_uuid_field("abc-123-def")
        self.assertEqual(result, "abc-123-def")

    def test_convert_uuid_none(self):
        """Test conversion of None"""
        result = convert_uuid_field(None)
        self.assertIsNone(result)


class TreeToFlatConversionTests(TestCase):
    """Test tree structure to flat dictionary conversion"""

    def test_simple_tree_conversion(self):
        """Test converting a simple tree with no children"""
        tree = {
            "id": {"__uuid__": "task-1"},
            "task_spec": "Start",
            "state": 64,
            "triggered": False,
            "data": {},
            "internal_data": {},
            "children": [],
            "last_state_change": 1234567890.0,
        }

        result = tree_to_flat(tree)

        self.assertIn("task-1", result)
        self.assertEqual(result["task-1"]["id"], "task-1")
        self.assertEqual(result["task-1"]["task_spec"], "Start")
        self.assertIsNone(result["task-1"]["parent"])
        self.assertEqual(result["task-1"]["children"], [])

    def test_nested_tree_conversion(self):
        """Test converting a tree with nested children"""
        tree = {
            "id": {"__uuid__": "parent-task"},
            "task_spec": "Root",
            "state": 64,
            "triggered": False,
            "data": {},
            "internal_data": {},
            "children": [
                {
                    "id": {"__uuid__": "child-task-1"},
                    "task_spec": "script_task",
                    "state": 32,
                    "triggered": False,
                    "data": {},
                    "internal_data": {},
                    "children": [],
                    "last_state_change": 1234567891.0,
                },
                {
                    "id": {"__uuid__": "child-task-2"},
                    "task_spec": "gateway_merge",
                    "state": 32,
                    "triggered": False,
                    "data": {},
                    "internal_data": {},
                    "children": [],
                    "last_state_change": 1234567892.0,
                },
            ],
            "last_state_change": 1234567890.0,
        }

        result = tree_to_flat(tree)

        # Should have 3 tasks
        self.assertEqual(len(result), 3)

        # Parent task
        self.assertIn("parent-task", result)
        self.assertEqual(
            result["parent-task"]["children"], ["child-task-1", "child-task-2"]
        )

        # Child tasks
        self.assertIn("child-task-1", result)
        self.assertEqual(result["child-task-1"]["parent"], "parent-task")

        self.assertIn("child-task-2", result)
        self.assertEqual(result["child-task-2"]["parent"], "parent-task")


class FormatDetectionTests(TestCase):
    """Test format version detection"""

    def test_detect_v1_format(self):
        """Test detection of v1 format"""
        v1_data = {
            "data": {},
            "task_tree": {"id": "123", "children": []},
            "last_task": {"__uuid__": "456"},
            "success": True,
        }

        result = detect_format_version(json.dumps(v1_data))
        self.assertEqual(result, "v1")

    def test_detect_v3_format(self):
        """Test detection of v3 format"""
        v3_data = {
            "data": {},
            "tasks": {"123": {"id": "123"}},
            "last_task": "456",
            "success": True,
            "typename": "BpmnWorkflow",
        }

        result = detect_format_version(json.dumps(v3_data))
        self.assertEqual(result, "v3")

    def test_detect_unknown_format(self):
        """Test detection of unknown format"""
        unknown_data = {"some": "data"}

        result = detect_format_version(json.dumps(unknown_data))
        self.assertEqual(result, "unknown")


class ValidationTests(TestCase):
    """Test v3 structure validation"""

    def test_validate_valid_v3_structure(self):
        """Test validation of valid v3 structure"""
        v3_obj = {
            "data": {},
            "correlations": {},
            "last_task": "task-1",
            "success": True,
            "completed": False,
            "tasks": {"task-1": {"id": "task-1", "typename": "Task"}},
            "root": "task-1",
            "subprocess_specs": {},
            "subprocesses": {},
            "bpmn_events": [],
            "typename": "BpmnWorkflow",
            "serializer_version": "1.4",
        }

        is_valid, errors = validate_v3_structure(v3_obj)
        self.assertTrue(is_valid)
        self.assertEqual(errors, [])

    def test_validate_missing_required_fields(self):
        """Test validation fails with missing fields"""
        v3_obj = {"data": {}, "tasks": {}}

        is_valid, errors = validate_v3_structure(v3_obj)
        self.assertFalse(is_valid)
        self.assertGreater(len(errors), 0)
        self.assertIn("Missing required field", errors[0])

    def test_validate_invalid_root_task(self):
        """Test validation fails when root task not in tasks"""
        v3_obj = {
            "data": {},
            "correlations": {},
            "last_task": "task-1",
            "success": True,
            "completed": False,
            "tasks": {"task-1": {"id": "task-1", "typename": "Task"}},
            "root": "non-existent-task",
            "subprocess_specs": {},
            "subprocesses": {},
            "bpmn_events": [],
            "typename": "BpmnWorkflow",
            "serializer_version": "1.4",
        }

        is_valid, errors = validate_v3_structure(v3_obj)
        self.assertFalse(is_valid)
        self.assertTrue(any("Root task" in err for err in errors))


class FullMigrationTests(TestCase):
    """Test complete migration workflow"""

    def setUp(self):
        """Set up test data"""
        # Create minimal v1 workflow data
        self.v1_data = {
            "data": {
                "status_name": {
                    "__bytes__": base64.b64encode(pickle.dumps("Huisbezoek")).decode()
                },
            },
            "task_tree": {
                "id": {"__uuid__": "root-task"},
                "task_spec": "Root",
                "state": 64,
                "triggered": False,
                "data": {},
                "internal_data": {},
                "children": [
                    {
                        "id": {"__uuid__": "child-task"},
                        "task_spec": "script_start_visit",
                        "state": 32,
                        "triggered": False,
                        "data": {
                            "theme": {
                                "__bytes__": base64.b64encode(
                                    pickle.dumps({"value": "theme_kamerverhuur"})
                                ).decode()
                            }
                        },
                        "internal_data": {},
                        "children": [],
                        "last_state_change": 1234567891.0,
                    }
                ],
                "last_state_change": 1234567890.0,
            },
            "last_task": {"__uuid__": "child-task"},
            "success": True,
        }

    def test_full_migration(self):
        """Test complete migration from v1 to v3"""
        v1_json = json.dumps(self.v1_data)
        v3_json = migrate_v1_to_v3(v1_json)
        v3_obj = json.loads(v3_json)

        # Check structure
        self.assertIn("tasks", v3_obj)
        self.assertIn("root", v3_obj)
        self.assertIn("typename", v3_obj)
        self.assertEqual(v3_obj["typename"], "BpmnWorkflow")

        # Check tasks
        self.assertEqual(len(v3_obj["tasks"]), 2)
        self.assertIn("root-task", v3_obj["tasks"])
        self.assertIn("child-task", v3_obj["tasks"])

        # Check unpickled data
        self.assertEqual(v3_obj["data"]["status_name"], "Huisbezoek")
        self.assertEqual(
            v3_obj["tasks"]["child-task"]["data"]["theme"],
            {"value": "theme_kamerverhuur"},
        )

        # Check typename inference
        self.assertEqual(v3_obj["tasks"]["root-task"]["typename"], "Task")
        self.assertEqual(v3_obj["tasks"]["child-task"]["typename"], "ScriptTask")

    def test_migration_raises_on_non_v1_data(self):
        """Test migration raises error for non-v1 data"""
        v3_data = {"tasks": {}, "typename": "BpmnWorkflow"}

        with self.assertRaises(ValueError):
            migrate_v1_to_v3(json.dumps(v3_data))

    def test_migration_raises_on_invalid_json(self):
        """Test migration raises error for invalid JSON"""
        with self.assertRaises(ValueError):
            migrate_v1_to_v3("invalid json {")


class MigrationStatsTests(TestCase):
    """Test migration statistics generation"""

    def test_get_migration_stats(self):
        """Test getting migration statistics"""
        v1_data = {
            "data": {
                "field1": {
                    "__bytes__": base64.b64encode(pickle.dumps("value1")).decode()
                },
                "field2": {
                    "__bytes__": base64.b64encode(pickle.dumps("value2")).decode()
                },
            },
            "task_tree": {
                "id": {"__uuid__": "root"},
                "task_spec": "Root",
                "state": 64,
                "triggered": False,
                "data": {},
                "internal_data": {},
                "children": [
                    {
                        "id": {"__uuid__": "task1"},
                        "task_spec": "script_task",
                        "state": 32,
                        "triggered": False,
                        "data": {},
                        "internal_data": {},
                        "children": [],
                        "last_state_change": 1234567891.0,
                    }
                ],
                "last_state_change": 1234567890.0,
            },
            "last_task": {"__uuid__": "task1"},
            "success": True,
        }

        v1_json = json.dumps(v1_data)
        v3_json = migrate_v1_to_v3(v1_json)

        stats = get_migration_stats(v1_json, v3_json)

        self.assertEqual(stats["v1_task_count"], 2)
        self.assertEqual(stats["v3_task_count"], 2)
        self.assertTrue(stats["task_count_match"])
        self.assertEqual(stats["unpickled_fields"], 2)
        self.assertIn("task_type_distribution", stats)
        self.assertEqual(stats["root_task"], "root")
        self.assertEqual(stats["last_task"], "task1")


class WorkflowModelIntegrationTests(TestCase):
    """Integration tests with CaseWorkflow model"""

    def setUp(self):
        """Set up test workflow"""
        self.theme = baker.make(CaseTheme, name=settings.DEFAULT_THEME)
        self.case = baker.make(Case, theme=self.theme)

        # Create v1 format data
        self.v1_data = {
            "data": {},
            "task_tree": {
                "id": {"__uuid__": "root-task"},
                "task_spec": "Root",
                "state": 64,
                "triggered": False,
                "data": {},
                "internal_data": {},
                "children": [],
                "last_state_change": 1234567890.0,
            },
            "last_task": {"__uuid__": "root-task"},
            "success": True,
        }

    def test_is_v1_format_with_workflow(self):
        """Test v1 format detection with CaseWorkflow"""
        # Test with dict directly (as it would be stored in model)
        self.assertTrue(is_v1_format(self.v1_data))

        # Also test with JSON string (as it might be passed)
        v1_json = json.dumps(self.v1_data)
        self.assertTrue(is_v1_format(v1_json))

    def test_is_v1_format_with_v3_workflow(self):
        """Test v3 format detection with CaseWorkflow"""
        v3_data = {
            "tasks": {"root": {"id": "root", "typename": "Task"}},
            "root": "root",
            "typename": "BpmnWorkflow",
        }

        workflow = baker.make(
            CaseWorkflow, case=self.case, serialized_workflow_state=v3_data
        )

        self.assertFalse(is_v1_format(workflow.serialized_workflow_state))


class EdgeCaseTests(TestCase):
    """Test edge cases and error handling"""

    def test_empty_tree(self):
        """Test handling of empty tree"""
        v1_data = {"data": {}, "task_tree": {}, "last_task": None, "success": True}

        with self.assertRaises(ValueError):
            migrate_v1_to_v3(json.dumps(v1_data))

    def test_task_without_id(self):
        """Test handling of task without ID"""
        tree = {"task_spec": "NoIdTask", "children": []}

        result = tree_to_flat(tree)
        self.assertEqual(len(result), 0)  # Should skip task without ID

    def test_deeply_nested_tree(self):
        """Test handling of deeply nested tree"""
        # Create a deeply nested tree (10 levels)
        tree = {
            "id": {"__uuid__": "level-0"},
            "task_spec": "Root",
            "state": 64,
            "triggered": False,
            "data": {},
            "internal_data": {},
            "children": [],
            "last_state_change": 1234567890.0,
        }

        current = tree
        for i in range(1, 10):
            child = {
                "id": {"__uuid__": f"level-{i}"},
                "task_spec": f"Task_{i}",
                "state": 32,
                "triggered": False,
                "data": {},
                "internal_data": {},
                "children": [],
                "last_state_change": 1234567890.0 + i,
            }
            current["children"] = [child]
            current = child

        result = tree_to_flat(tree)
        self.assertEqual(len(result), 10)
