import os
from typing import Any

from azure.monitor.opentelemetry.exporter import (
    AzureMonitorLogExporter,
    AzureMonitorTraceExporter,
)
from opentelemetry import trace
from opentelemetry.instrumentation.django import DjangoInstrumentor
from opentelemetry.instrumentation.psycopg2 import Psycopg2Instrumentor
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor


def start_logging():
    LOGGING_HANDLERS: dict[str, dict[str, Any]] = {
        "console": {
            "class": "logging.StreamHandler",
        },
    }
    LOGGER_HANDLERS = [
        "console",
    ]

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    APPLICATIONINSIGHTS_CONNECTION_STRING = os.getenv(
        "APPLICATIONINSIGHTS_CONNECTION_STRING"
    )

    def response_hook(span, request, response):
        if (
            span
            and span.is_recording()
            and hasattr(request, "user")
            and request.user is not None
            and hasattr(request.user, "is_authenticated")
            and request.user.is_authenticated is True
        ):
            span.set_attributes({"django.user.name": request.user.username})

    MONITOR_SERVICE_NAME = "zaken-backend"
    resource: Resource = Resource.create({"service.name": MONITOR_SERVICE_NAME})

    tracer_provider: TracerProvider = TracerProvider(resource=resource)
    trace.set_tracer_provider(tracer_provider)
    if APPLICATIONINSIGHTS_CONNECTION_STRING:
        span_exporter: AzureMonitorTraceExporter = AzureMonitorTraceExporter(
            connection_string=APPLICATIONINSIGHTS_CONNECTION_STRING
        )
        tracer_provider.add_span_processor(
            BatchSpanProcessor(span_exporter=span_exporter)
        )
        log_exporter: AzureMonitorLogExporter = AzureMonitorLogExporter(
            connection_string=APPLICATIONINSIGHTS_CONNECTION_STRING
        )
        logger_provider: LoggerProvider = LoggerProvider(resource=resource)
        logger_provider.add_log_record_processor(
            BatchLogRecordProcessor(log_exporter, schedule_delay_millis=3000)
        )

        class AzureLoggingHandler(LoggingHandler):
            def __init__(self):
                super().__init__(logger_provider=logger_provider)

        LOGGING_HANDLERS.update(
            {
                "azure": {
                    "()": AzureLoggingHandler,
                    "formatter": "elaborate",
                    "level": os.getenv("LOGGING_LEVEL", "WARNING"),
                }
            }
        )

        LOGGER_HANDLERS.append("azure")
        if os.getenv("LOGGING_LEVEL", "WARNING") == "DEBUG":
            Psycopg2Instrumentor().instrument(
                tracer_provider=tracer_provider, skip_dep_check=True
            )
        DjangoInstrumentor().instrument(
            tracer_provider=tracer_provider, response_hook=response_hook
        )
