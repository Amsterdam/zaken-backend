from django.apps import AppConfig


class WorkflowConfig(AppConfig):
    name = "apps.workflow"

    def ready(self):
        import apps.workflow.signals  # noqa
