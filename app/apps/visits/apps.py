from django.apps import AppConfig


class VisitsConfig(AppConfig):
    name = "apps.visits"

    def ready(self):
        import apps.visits.signals
