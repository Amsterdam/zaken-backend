from apps.workflow.serializers import WorkflowSpecConfigSerializer
from apps.workflow.utils import workflow_spec_paths_inspect
from django.conf import settings
from django.test import TestCase


class WorkflowConfTest(TestCase):
    def test_settings_conf_structure(self):
        """
        Tests if the structure of the conf is valid, based on the WorkflowSpecConfigSerializer
        """

        serializer = WorkflowSpecConfigSerializer(data=settings.WORKFLOW_SPEC_CONFIG)

        self.assertEquals(serializer.is_valid(), True)

    def test_settings_conf_paths(self):
        """
        Tests if paths defined in the conf exist on the filesystem and tests if the workflow can be started by the workflow type name
        """

        serializer = WorkflowSpecConfigSerializer(data=settings.WORKFLOW_SPEC_CONFIG)

        self.assertEquals(serializer.is_valid(), True)

        paths = workflow_spec_paths_inspect(settings.WORKFLOW_SPEC_CONFIG)

        non_valid_paths = [p.get("path") for p in paths if not p.get("workflow_data")]

        self.assertEquals(non_valid_paths, [])

    def test_settings_conf_messages(self):
        """
        Tests if the messages used in conf can be executed and if so,
        does this result in a change in the workflow, if so the message is valid
        """

        serializer = WorkflowSpecConfigSerializer(data=settings.WORKFLOW_SPEC_CONFIG)

        self.assertEquals(serializer.is_valid(), True)

        paths = workflow_spec_paths_inspect(settings.WORKFLOW_SPEC_CONFIG)

        non_valid_paths = [p.get("path") for p in paths if not p.get("workflow_data")]

        self.assertEquals(non_valid_paths, [])
        valid_paths_messages = [
            {
                "messages": p.get("workflow_data", {}).get("messages"),
                "path": p.get("path"),
            }
            for p in paths
            if p.get("workflow_data")
        ]

        invalid_messages_paths = [
            {"message": m, "path": path.get("path")}
            for path in valid_paths_messages
            for m in path.get("messages", [])
            if not m.get("exists")
        ]

        self.assertEquals(invalid_messages_paths, [])

    def test_workflow_tree(self):
        """
        Tests if the bpmn trees of all the versions/types do not return errors.
        """

        serializer = WorkflowSpecConfigSerializer(data=settings.WORKFLOW_SPEC_CONFIG)

        self.assertEquals(serializer.is_valid(), True)

        paths = workflow_spec_paths_inspect(settings.WORKFLOW_SPEC_CONFIG)

        non_valid_paths = [p.get("path") for p in paths if not p.get("workflow_data")]

        self.assertEquals(non_valid_paths, [])
        workflow_tree_inspect = [
            {
                "path": p.get("path"),
                "tree_valid": p.get("workflow_data", {}).get("tree_valid"),
            }
            for p in paths
            if p.get("workflow_data")
        ]

        invalid_workflow_trees = [
            p.get("path") for p in workflow_tree_inspect if not p.get("tree_valid")
        ]
        self.assertEquals(invalid_workflow_trees, [])
