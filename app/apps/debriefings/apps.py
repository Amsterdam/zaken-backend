from django.apps import AppConfig


class DebriefingsConfig(AppConfig):
    name = "apps.debriefings"

    def ready(self):
        import apps.debriefings.signals  # noqa
