from django.apps import AppConfig


class DebriefingsConfig(AppConfig):
    name = "debriefings"

    def ready(self):
        import apps.debriefings.signals
