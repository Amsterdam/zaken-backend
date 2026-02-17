import os

from azure.monitor.opentelemetry import configure_azure_monitor
from opentelemetry.instrumentation.django import DjangoInstrumentor
from opentelemetry.instrumentation.psycopg2 import Psycopg2Instrumentor
from opentelemetry.sdk.trace.sampling import Decision, Sampler, SamplingResult


class ExcludeHealthCheckSampler(Sampler):
    def should_sample(
        self,
        context,
        trace_id,
        name,
        kind=None,
        attributes=None,
        links=None,
        trace_state=None,
    ):
        if attributes:
            url = attributes.get("http.target") or attributes.get("url.path", "")
            if url in ("/", "/health"):
                return SamplingResult(Decision.DROP)
        return SamplingResult(Decision.RECORD_AND_SAMPLE)

    def get_description(self):
        return "ExcludeHealthCheckSampler"


def start_logging():

    APPLICATIONINSIGHTS_CONNECTION_STRING = os.getenv(
        "APPLICATIONINSIGHTS_CONNECTION_STRING"
    )

    if APPLICATIONINSIGHTS_CONNECTION_STRING is None:
        return

    configure_azure_monitor(
        connection_string=APPLICATIONINSIGHTS_CONNECTION_STRING,
        service_name="zaken-backend",
        sampler=ExcludeHealthCheckSampler(),
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
