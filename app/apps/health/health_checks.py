import logging

import requests
from config.celery import debug_task
from django.conf import settings
from health_check.backends import BaseHealthCheckBackend
from health_check.exceptions import ServiceUnavailable
from utils.api_queries_vakantieverhuur_registraties import (
    get_bag_vakantieverhuur_registrations,
    get_bsn_vakantieverhuur_registrations,
    get_vakantieverhuur_registration,
)

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
            response = DecosJoinRequest().get()
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

    redis_url = settings.REDIS_URL

    def check_status(self):
        """Check Redis service by pinging the redis instance with a redis connection."""
        logger.info("Got %s as the redis_url. Connecting to redis...", self.redis_url)
        logger.info("Attempting to connect to redis...")

        try:
            from django_redis import get_redis_connection

            connection = get_redis_connection("default")
            logger.debug("Redis Connection")
            logger.debug(connection)

            result = connection.ping()
            logger.debug("Redis Ping")
            logger.debug(result)

        except Exception as e:
            logger.error(e)
            self.add_error(ServiceUnavailable("Unknown error"), e)
        else:
            logger.info("Connection established. Redis is healthy.")


class OpenZaakClientCheck(BaseHealthCheckBackend):
    """
    Tests the Open Zaak client
    """

    def check_status(self):
        try:
            from zgw_consumers.constants import APITypes
            from zgw_consumers.models import Service

            ztc_client = (
                Service.objects.filter(api_type=APITypes.ztc).get().build_client()
            )

            results = ztc_client.list(
                "catalogus", {"rsin": settings.DEFAULT_CATALOGUS_RSIN}
            )
            assert results["count"] != 0, "The default catalogus doesn't exist"

            results = ztc_client.list(
                "zaaktype", {"identificatie": settings.DEFAULT_TEAM}
            )
            assert results["count"] != 0, "The default casetype doesn't exist"

        except Exception as e:
            self.add_error(ServiceUnavailable("Failed"), e)


class VakantieVerhuurRegistratieCheck(BaseHealthCheckBackend):
    """
    Check if a connection can be made with the Vakantieverhuur Registratie API
    """

    critical_service = False
    verbose_name = "Vakantieverhuur Registratie API"

    def check_status(self):

        try:
            registration = get_vakantieverhuur_registration(
                settings.VAKANTIEVERHUUR_REGISTRATIE_API_HEALTH_CHECK_REGISTRATION_NUMBER
            )
            assert bool(
                registration
            ), "The registration data is empty and could not be retrieved"

            bsn_registrations = get_bsn_vakantieverhuur_registrations(
                settings.VAKANTIEVERHUUR_REGISTRATIE_API_HEALTH_CHECK_BSN
            )
            assert (
                len(bsn_registrations) > 0
            ), "The registration data is empty and could not be retrieved using the BSN number"

            bag_registrations = get_bag_vakantieverhuur_registrations(
                settings.VAKANTIEVERHUUR_REGISTRATIE_API_HEALTH_CHECK_BAG_ID
            )
            assert (
                len(bag_registrations) > 0
            ), "The registration data is empty and could not be retrieved using the BAG id"

        except Exception as e:
            logger.error(e)
            self.add_error(ServiceUnavailable("Failed"), e)
        else:
            logger.info(
                "Connection established. Vakantieverhuur Registratie API connection is healthy."
            )
