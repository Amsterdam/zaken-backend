import logging

import requests
from config.celery import debug_task
from django.conf import settings
from health_check.backends import BaseHealthCheckBackend
from health_check.exceptions import ServiceUnavailable
from requests.exceptions import HTTPError
from utils.api_queries_toeristische_verhuur import (
    get_bag_vakantieverhuur_registrations,
    get_bsn_vakantieverhuur_registrations,
    get_vakantieverhuur_meldingen,
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

    def get_api_url(self):
        return self.api_url

    def check_status(self):
        """Check service by opening and closing a broker channel."""
        logger.info("Checking status of API url...")
        api_url = self.get_api_url()
        assert api_url, "The given api_url should be set"
        try:
            response = requests.get(api_url, timeout=3)
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
        except HTTPError as e:
            logger.error(e)
            self.add_error(ServiceUnavailable(f"Service not found. {api_url}"))
        except BaseException as e:
            logger.error(e)
            self.add_error(ServiceUnavailable("Unknown error"), e)
        else:
            logger.info("Connection established. API is healthy.")

    def identifier(self):
        if self.verbose_name:
            return self.verbose_name

        return self.__class__.__name__


class BAGAtlasServiceCheck(APIServiceCheckBackend):
    """
    Endpoint for checking the BAG Atlas Service API Endpoint
    """

    critical_service = True
    api_url = settings.BAG_API_SEARCH_URL
    verbose_name = "BAG Atlas API"


class BAGNummeraanduidingenServiceCheck(APIServiceCheckBackend):
    """
    Endpoint for checking the BAG Nummeraanduidingen Service API
    """

    critical_service = True
    api_url = settings.BAG_API_NUMMERAANDUIDING_SEARCH_URL
    verbose_name = "BAG Nummeraanduidingen API"


class BAGVerblijfsobjectServiceCheck(APIServiceCheckBackend):
    """
    Endpoint for checking the BAG Verblijfsobject Service API Endpoint
    """

    critical_service = True
    api_url = settings.BAG_API_VERBLIJFSOBJECT_URL
    verbose_name = "BAG Verblijfsobject API"


class BRPServiceCheck(APIServiceCheckBackend):
    """
    Endpoint for checking the BRP Service API Endpoint
    """

    critical_service = True
    api_url = settings.BRP_API_URL
    verbose_name = "BRP API"


class CeleryExecuteTask(BaseHealthCheckBackend):
    def check_status(self):
        result = debug_task.apply_async(ignore_result=False)
        assert result, "Debug task executes successfully"


class Belastingdienst(BaseHealthCheckBackend):
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


class OpenZaakZaken(APIServiceCheckBackend):
    """
    Endpoint for checking Keycloak
    """

    critical_service = True
    verbose_name = "Open-zaak zaken (ZRC)"

    def get_api_url(self):
        from zgw_consumers.constants import APITypes
        from zgw_consumers.models import Service

        zaken_service = Service.objects.filter(api_type=APITypes.zrc).get()
        return zaken_service.api_root


class OpenZaakZakenCatalogus(APIServiceCheckBackend):
    """
    Endpoint for checking Keycloak
    """

    critical_service = True
    verbose_name = "Open-zaak catalogus (ZTC)"

    def get_api_url(self):
        from zgw_consumers.constants import APITypes
        from zgw_consumers.models import Service

        catalogi_service = Service.objects.filter(api_type=APITypes.ztc).get()
        return catalogi_service.api_root


class OpenZaakZakenAlfresco(APIServiceCheckBackend):
    """
    Endpoint for checking Keycloak
    """

    critical_service = True
    verbose_name = "Open-zaak Alfresco (DRC)"

    def get_api_url(self):
        from zgw_consumers.constants import APITypes
        from zgw_consumers.models import Service

        documenten_service = Service.objects.filter(api_type=APITypes.drc).get()
        return documenten_service.api_root


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


class Toeristischeverhuur(BaseHealthCheckBackend):
    """
    Check if a connection can be made with the toeristischeverhuur.nl API
    """

    critical_service = True
    verbose_name = "Toeristischeverhuur.nl"

    def check_status(self):
        params = {
            "pageNumber": 1,
            "pageSize": 1000,
        }

        try:
            response = get_vakantieverhuur_meldingen(
                settings.VAKANTIEVERHUUR_TOERISTISCHE_VERHUUR_API_HEALTH_CHECK_BAG_ID,
                query_params=params,
            )
            assert response, "Could not reach Toeristischeverhuur.nl"

        except Exception as e:
            logger.error(e)
            self.add_error(ServiceUnavailable("Failed"), e)
        else:
            logger.info(
                "Connection established. Toeristischeverhuur.nl API connection is healthy."
            )
