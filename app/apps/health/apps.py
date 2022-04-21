from django.apps import AppConfig
from health_check.plugins import plugin_dir


class HealthConfig(AppConfig):
    name = "apps.health"

    def ready(self):
        from .health_checks import (
            BAGServiceCheck,
            BelastingDienstCheck,
            BRPServiceCheck,
            CatalogiEndpointCheck,
            CeleryExecuteTask,
            DecosJoinCheck,
            DocumentenEndpointCheck,
            KeycloakCheck,
            ZakenEndpointCheck,
        )

        plugin_dir.register(BAGServiceCheck)
        plugin_dir.register(BRPServiceCheck)
        plugin_dir.register(BelastingDienstCheck)
        plugin_dir.register(CeleryExecuteTask)
        plugin_dir.register(KeycloakCheck)
        plugin_dir.register(ZakenEndpointCheck)
        plugin_dir.register(DocumentenEndpointCheck)
        plugin_dir.register(CatalogiEndpointCheck)
        # plugin_dir.register(VakantieVerhuurRegistratieCheck)
        plugin_dir.register(DecosJoinCheck)
