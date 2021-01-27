from django.apps import AppConfig


class OpenzaakConfig(AppConfig):
    name = "apps.openzaak"

    def ready(self):
        from django.core import management

        management.call_command("initialize_openzaak")
