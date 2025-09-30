import os
import xml.etree.ElementTree as ET

from apps.workflow.serializers import WorkflowSpecConfigSerializer
from apps.workflow.utils import get_workflow_path, get_workflow_spec
from django.conf import settings
from django.test import TestCase
from SpiffWorkflow.camunda.parser import CamundaParser


class WorkflowConfTest(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.serializer = WorkflowSpecConfigSerializer(
            data=settings.WORKFLOW_SPEC_CONFIG
        )
        cls.serializer.is_valid(raise_exception=True)
        cls.workflow_spec_config = cls.serializer.validated_data

    def _iter_workflow_versions(self):
        for theme, types in self.workflow_spec_config.items():
            for workflow_type, type_config in types.items():
                for version, version_config in type_config.get("versions", {}).items():
                    yield theme, workflow_type, version, version_config

    def _collect_message_names(self, theme, workflow_type, version):
        workflow_path = get_workflow_path(workflow_type, theme, version)
        message_names = set()
        parser = CamundaParser()
        for filename in os.listdir(workflow_path):
            if not filename.lower().endswith(".bpmn"):
                continue
            file_path = os.path.join(workflow_path, filename)
            parser.add_bpmn_file(file_path)
            tree = ET.parse(file_path)
            root = tree.getroot()
            for message_node in root.findall(
                ".//{http://www.omg.org/spec/BPMN/20100524/MODEL}message"
            ):
                name = message_node.get("name")
                if name:
                    message_names.add(name)
        parser.get_spec(workflow_type)
        return message_names

    def test_settings_conf_structure(self):
        """
        Tests if the structure of the conf is valid, based on the WorkflowSpecConfigSerializer
        """

        serializer = WorkflowSpecConfigSerializer(data=settings.WORKFLOW_SPEC_CONFIG)
        self.assertEqual(serializer.is_valid(), True)

    def test_settings_conf_paths(self):
        """
        Tests if paths defined in the conf exist on the filesystem and tests if the workflow can be started by the workflow type name
        """

        missing = []
        for theme, workflow_type, version, _ in self._iter_workflow_versions():
            workflow_path = get_workflow_path(workflow_type, theme, version)
            if not os.path.isdir(workflow_path):
                missing.append(
                    {
                        "theme": theme,
                        "workflow_type": workflow_type,
                        "version": version,
                        "reason": "directory-missing",
                    }
                )
                continue
            has_bpmn_files = any(
                filename.lower().endswith(".bpmn")
                for filename in os.listdir(workflow_path)
            )
            if not has_bpmn_files:
                missing.append(
                    {
                        "theme": theme,
                        "workflow_type": workflow_type,
                        "version": version,
                        "reason": "no-bpmn-files",
                    }
                )

        self.assertListEqual(missing, [])

    def test_all_bpmn_specs_parse(self):
        """Every configured workflow should parse into a SpiffWorkflow spec."""

        failures = []
        for theme, workflow_type, version, _ in self._iter_workflow_versions():
            workflow_path = get_workflow_path(workflow_type, theme, version)
            try:
                get_workflow_spec(workflow_path, workflow_type)
            except Exception as exc:  # pragma: no cover - diagnostic path
                failures.append(
                    {
                        "theme": theme,
                        "workflow_type": workflow_type,
                        "version": version,
                        "error": str(exc),
                    }
                )

        self.assertListEqual(failures, [])

    def test_configured_messages_exist_in_bpmn(self):
        """Configured messages should match message definitions in the BPMN files."""

        missing = []
        for (
            theme,
            workflow_type,
            version,
            version_config,
        ) in self._iter_workflow_versions():
            config_messages = version_config.get("messages", {})
            if not config_messages:
                continue
            message_names = self._collect_message_names(theme, workflow_type, version)
            for message_name in config_messages.keys():
                if message_name not in message_names:
                    missing.append(
                        {
                            "theme": theme,
                            "workflow_type": workflow_type,
                            "version": version,
                            "message": message_name,
                        }
                    )

        self.assertListEqual(missing, [])
