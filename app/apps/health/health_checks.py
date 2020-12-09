import logging

import requests
from config.celery import debug_task
from django.conf import settings
from health_check.backends import BaseHealthCheckBackend
from health_check.exceptions import ServiceUnavailable
from kombu import Connection

logger = logging.getLogger(__name__)


class APIServiceCheckBackend(BaseHealthCheckBackend):
    """
    Generic base class for checking API services
    """

    critical_service = False
    api_url = None
    verbose_name = None

    def check_status(self):
        """Check service by opening and closing a broker channel."""
        logger.debug("Checking status of API url...")
        try:
            assert self.api_url, "The given api_url should be set"
            response = requests.get(self.api_url)
            response.raise_for_status()
        except AssertionError as e:
            self.add_error(
                ServiceUnavailable("The given API endpoint has not been set"),
                e,
            )
        except ConnectionRefusedError as e:
            self.add_error(
                ServiceUnavailable("Unable to connect to API: Connection was refused."),
                e,
            )
        except BaseException as e:
            self.add_error(ServiceUnavailable("Unknown error"), e)
        else:
            logger.debug("Connection established. API is healthy.")

    def identifier(self):
        if self.verbose_name:
            return self.verbose_name

        return self.__class__.__name__


class BAGServiceCheck(APIServiceCheckBackend):
    """
    Endpoint for checking the BAG Service API Endpoint
    """

    critical_service = True
    api_url = settings.BAG_API_SEARCH_URL
    verbose_name = "BAG API Endpoint"


class CeleryTest(BaseHealthCheckBackend):
    def check_status(self):
        debug_task.delay()


class DebugRabbitMQHealthCheck(BaseHealthCheckBackend):
    """Health check for RabbitMQ."""

    def check_status(self):
        """Check RabbitMQ service by opening and closing a broker channel."""
        logger.info("Checking for a broker_url on django settings...")

        broker_url = getattr(settings, "BROKER_URL", None)

        logger.info("Got %s as the broker_url. Connecting to rabbit...", broker_url)
        print("Got %s as the broker_url. Connecting to rabbit...", broker_url)
        logger.info("Attempting to connect to rabbit...")
        print("Attempting to connect to rabbit...")
        try:
            # conn is used as a context to release opened resources later
            with Connection(broker_url) as conn:
                conn.connect()
        except Exception as e:
            print(e)
            logger.error(e)
            self.add_error("Debug Error", e)
