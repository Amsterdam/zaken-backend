from django.apps import AppConfig
from django.conf import settings


class OpenzaakConfig(AppConfig):
    name = "apps.openzaak"
    verbose_name = "Openzaak"
    app_label = "openzaak"

    def ready(self):
        if settings.OPENZAAK_ENABLED:
            import apps.openzaak.signals  # noqa
