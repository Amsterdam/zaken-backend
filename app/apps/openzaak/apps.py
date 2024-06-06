from django.apps import AppConfig
from utils.openzaak_enabled import is_openzaak_enabled


class OpenzaakConfig(AppConfig):
    name = "apps.openzaak"
    verbose_name = "Openzaak"
    app_label = "openzaak"

    def ready(self):
        if is_openzaak_enabled():
            import apps.openzaak.signals  # noqa
