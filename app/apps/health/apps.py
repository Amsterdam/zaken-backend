from django.apps import AppConfig
from health_check.plugins import plugin_dir


class HealthConfig(AppConfig):
    name = "apps.health"

    def ready(self):
        from .health_checks import (  # OpenZaakZaken,; OpenZaakZakenAlfresco,; OpenZaakZakenCatalogus,
            BAGAtlasServiceCheck,
            BAGNummeraanduidingenServiceCheck,
            BAGVerblijfsobjectServiceCheck,
            Belastingdienst,
            BRPServiceCheck,
            CeleryExecuteTask,
            DecosJoinCheck,
            KeycloakCheck,
            PowerBrowser,
            Toeristischeverhuur,
        )

        plugin_dir.register(BAGAtlasServiceCheck)
        plugin_dir.register(BAGNummeraanduidingenServiceCheck)
        plugin_dir.register(BAGVerblijfsobjectServiceCheck)
        plugin_dir.register(BRPServiceCheck)
        plugin_dir.register(Belastingdienst)
        plugin_dir.register(CeleryExecuteTask)
        plugin_dir.register(DecosJoinCheck)
        plugin_dir.register(KeycloakCheck)
        # plugin_dir.register(OpenZaakZaken)
        # plugin_dir.register(OpenZaakZakenAlfresco)
        # plugin_dir.register(OpenZaakZakenCatalogus)
        plugin_dir.register(PowerBrowser)
        plugin_dir.register(Toeristischeverhuur)
        # plugin_dir.register(VakantieVerhuurRegistratieCheck)
        plugin_dir.register(PowerBrowser)
        plugin_dir.register(DecosJoinCheck)
