from django.apps import AppConfig
from health_check.plugins import plugin_dir


class HealthConfig(AppConfig):
    name = "apps.health"

    def ready(self):
        from .health_checks import (
            BAGServiceCheck,
            BelastingDienstCheck,
            CeleryExecuteTask,
            DecosJoinCheck,
        )

        plugin_dir.register(BAGServiceCheck)
        plugin_dir.register(BelastingDienstCheck)
        plugin_dir.register(CeleryExecuteTask)
        plugin_dir.register(DecosJoinCheck)
