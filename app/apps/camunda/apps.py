from django.apps import AppConfig


class CamundaConfig(AppConfig):
    name = "apps.camunda"

    def ready(self):
        import apps.camunda.signals  # noqa
