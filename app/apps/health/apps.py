from django.apps import AppConfig
from health_check.plugins import plugin_dir


class HealthConfig(AppConfig):
    name = "apps.health"

    def ready(self):
        from .health_checks import (
            BAGServiceCheck,
            BelastingDienstCheck,
            CamundaServiceCheck,
            CeleryExecuteTask,
            DecosJoinCheck,
            KeycloakCheck,
        )

        plugin_dir.register(BAGServiceCheck)
        plugin_dir.register(BelastingDienstCheck)
        plugin_dir.register(CeleryExecuteTask)
        plugin_dir.register(DecosJoinCheck)
        plugin_dir.register(KeycloakCheck)
        plugin_dir.register(CamundaServiceCheck)
