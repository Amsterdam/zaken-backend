import os

from azure.monitor.opentelemetry import configure_azure_monitor
from opentelemetry.instrumentation.django import DjangoInstrumentor
from opentelemetry.instrumentation.psycopg2 import Psycopg2Instrumentor


def start_logging():

    APPLICATIONINSIGHTS_CONNECTION_STRING = os.getenv(
        "APPLICATIONINSIGHTS_CONNECTION_STRING"
    )

    if APPLICATIONINSIGHTS_CONNECTION_STRING is None:
        return

    os.environ["OTEL_PYTHON_DJANGO_EXCLUDED_URLS"] = "^/$|^/health$"
    configure_azure_monitor(
        connection_string=APPLICATIONINSIGHTS_CONNECTION_STRING,
        service_name="zaken-backend",
    )

    def response_hook(span, request, response):
        if not span or not span.is_recording():
            return

        if hasattr(request, "user") and getattr(
            request.user, "is_authenticated", False
        ):
            span.set_attribute("django.user.name", request.user.username)

    DjangoInstrumentor().uninstrument()
    DjangoInstrumentor().instrument(response_hook=response_hook)
    if os.getenv("LOGGING_LEVEL", "WARNING").upper() == "DEBUG":
        Psycopg2Instrumentor().instrument()
    else:
        Psycopg2Instrumentor().uninstrument()
