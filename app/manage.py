#!/usr/bin/env python
import os
import sys
from azure.monitor.opentelemetry import configure_azure_monitor
from opentelemetry.instrumentation.django import DjangoInstrumentor
from opentelemetry.instrumentation.logging import LoggingInstrumentor
from opentelemetry.instrumentation.psycopg2 import Psycopg2Instrumentor

if __name__ == "__main__":
    from django.core.management import execute_from_command_line

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    configure_azure_monitor(
        connection_string=os.environ['APPLICATIONINSIGHTS_CONNECTION_STRING']
    )
    LoggingInstrumentor().instrument(set_logging_format=True)
    DjangoInstrumentor().instrument(is_sql_commentor_enabled=True)
    Psycopg2Instrumentor().instrument()
    execute_from_command_line(sys.argv)
