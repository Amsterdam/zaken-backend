from django.apps import AppConfig


class SummonsConfig(AppConfig):
    name = "apps.summons"

    def ready(self):
        import apps.summons.signals  # noqa
