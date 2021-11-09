from rest_framework import status
from rest_framework.exceptions import APIException


class ServerError(APIException):
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    default_detail = "Er ging iets mis met het opslaan van de de informatie. Probeer het later nog eens."
    default_code = "server_error"
