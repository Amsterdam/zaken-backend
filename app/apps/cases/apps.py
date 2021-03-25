from django.apps import AppConfig


class CasesConfig(AppConfig):
    name = "apps.cases"

    def ready(self):
        import apps.cases.signals  # noqa
