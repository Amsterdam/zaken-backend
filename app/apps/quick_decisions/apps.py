from django.apps import AppConfig


class QuickDecisionsConfig(AppConfig):
    name = "apps.quick_decisions"

    def ready(self):
        import apps.quick_decisions.signals  # noqa
