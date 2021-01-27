from django.apps import AppConfig


class VisitsConfig(AppConfig):
    name = "visits"

    def ready(self):
        import apps.visits.signals
