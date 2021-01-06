import logging

import requests
from config.celery import debug_task
from django.conf import settings
from health_check.backends import BaseHealthCheckBackend
from health_check.exceptions import ServiceUnavailable
from kombu import Connection

from redis import exceptions, from_url

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
        logger.info("Checking status of API url...")
        try:
            assert self.api_url, "The given api_url should be set"
            response = requests.get(self.api_url, timeout=3)
            response.raise_for_status()
        except AssertionError as e:
            logger.error(e)
            self.add_error(
                ServiceUnavailable("The given API endpoint has not been set"),
                e,
            )
        except ConnectionRefusedError as e:
            logger.error(e)
            self.add_error(
                ServiceUnavailable("Unable to connect to API: Connection was refused."),
                e,
            )
        except BaseException as e:
            logger.error(e)
            self.add_error(ServiceUnavailable("Unknown error"), e)
        else:
            logger.info("Connection established. API is healthy.")

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


class CamundaServiceCheck(APIServiceCheckBackend):
    """
    Endpoint for checking the BAG Service API Endpoint
    """

    critical_service = True
    api_url = settings.CAMUNDA_HEALTH_CHECK_URL
    verbose_name = "Camunda Service"


class CeleryExecuteTask(BaseHealthCheckBackend):
    def check_status(self):
        result = debug_task.apply_async(ignore_result=False)
        assert result, "Debug task executes successfully"


class OpenZaakCheck(BaseHealthCheckBackend):
    """
    Tests an authenticated request to the OpenZaak instance
    """

    def check_status(self):
        from services.example.catalog.services import CatalogService

        try:
            CatalogService().get()
        except Exception as e:
            self.add_error(ServiceUnavailable("Failed"), e)


class BelastingDienstCheck(BaseHealthCheckBackend):
    """
    Tests an authenticated request to the Belastingdienst endpoint
    """

    def check_status(self):
        from apps.fines.api_queries_belastingen import get_fines

        try:
            # The id doesn't matter, as long an authenticated request is succesful.
            get_fines("foo-id")
        except Exception as e:
            self.add_error(ServiceUnavailable("Failed"), e)


class DecosJoinCheck(BaseHealthCheckBackend):
    """
    Tests an authenticated request to Decos Join
    """

    def check_status(self):
        from apps.permits.api_queries_decos_join import DecosJoinRequest

        try:
            # The address doesn't matter, as long an authenticated request is succesful.
            response = DecosJoinRequest().get_decos_object_with_address("foo")
            assert response, "Could not reach Decos Join"
        except Exception as e:
            self.add_error(ServiceUnavailable("Failed"), e)


class KeycloakCheck(APIServiceCheckBackend):
    """
    Endpoint for checking Keycloak
    """

    critical_service = True
    api_url = settings.OIDC_OP_JWKS_ENDPOINT
    verbose_name = "Keycloak"


class OpenZaakRedisHealthCheck(BaseHealthCheckBackend):
    """
    Redis used by Open Zaak check
    """

    redis_url = settings.OPEN_ZAAK_REDIS_HEALTH_CHECK_URL

    def check_status(self):
        """Check Redis service by pinging the redis instance with a redis connection."""
        logger.info("Got %s as the redis_url. Connecting to redis...", self.redis_url)

        logger.info("Attempting to connect to redis...")
        try:
            # conn is used as a context to release opened resources later
            with from_url(self.redis_url) as conn:
                conn.ping()  # exceptions may be raised upon ping
        except ConnectionRefusedError as e:
            logger.error(e)
            self.add_error(
                ServiceUnavailable(
                    "Unable to connect to Redis: Connection was refused."
                ),
                e,
            )
        except exceptions.TimeoutError as e:
            logger.error(e)
            self.add_error(
                ServiceUnavailable("Unable to connect to Redis: Timeout."), e
            )
        except exceptions.ConnectionError as e:
            logger.error(e)
            self.add_error(
                ServiceUnavailable("Unable to connect to Redis: Connection Error"), e
            )
        except BaseException as e:
            logger.error(e)
            self.add_error(ServiceUnavailable("Unknown error"), e)
        else:
            logger.info("Connection established. Redis is healthy.")
