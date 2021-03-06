from django.apps import AppConfig
from health_check.plugins import plugin_dir


class HealthConfig(AppConfig):
    name = "apps.health"

    def ready(self):
        from .health_checks import (  # CamundaServiceCheck,
            BAGServiceCheck,
            BelastingDienstCheck,
            CeleryExecuteTask,
            DecosJoinCheck,
            KeycloakCheck,
            OpenZaakClientCheck,
            OpenZaakRedisHealthCheck,
            VakantieVerhuurRegistratieCheck,
        )

        plugin_dir.register(BAGServiceCheck)
        plugin_dir.register(BelastingDienstCheck)
        plugin_dir.register(CeleryExecuteTask)
        plugin_dir.register(KeycloakCheck)
        plugin_dir.register(OpenZaakRedisHealthCheck)
        plugin_dir.register(OpenZaakClientCheck)
        # plugin_dir.register(VakantieVerhuurRegistratieCheck)
        plugin_dir.register(DecosJoinCheck)
        # plugin_dir.register(CamundaServiceCheck)
