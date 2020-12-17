from django.apps import AppConfig
from health_check.plugins import plugin_dir


class HealthConfig(AppConfig):
    name = "apps.health"

    def ready(self):
        from .health_checks import (
            BAGServiceCheck,
            CamundaServiceCheck,
            CeleryExecuteTask,
        )

        plugin_dir.register(BAGServiceCheck)
        plugin_dir.register(CeleryExecuteTask)
        plugin_dir.register(CamundaServiceCheck)
