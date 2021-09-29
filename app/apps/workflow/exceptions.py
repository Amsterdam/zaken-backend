from rest_framework import status
from rest_framework.exceptions import APIException


class ServiceUnavailable(APIException):
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    default_detail = "Er ging iets mis met het opslaan van de de informatie. Probeer het later nog eens."
    default_code = "service_unavailable"
