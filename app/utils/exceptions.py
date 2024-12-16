from apps.users.auth import InvalidTokenError
from redis.exceptions import TimeoutError as RedisTimeoutError
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler


class BaseException(Exception):
    default_message = "Error"

    def __init__(self, resp=None):
        resp = resp if resp else self.default_message
        self.args = (resp,)
        self.message = resp


class EventEmitterExistsError(BaseException):
    default_message = "Event Emitter exists"


class MKSPermissionsError(BaseException):
    default_message = "Je hebt geen rechten voor MKS"


class DistrictNotFoundError(Exception):
    pass


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if isinstance(exc, EventEmitterExistsError):
        return Response(
            {"message": "Deze taak is al eerder onvolledig afgerond."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    if isinstance(exc, MKSPermissionsError):
        return Response(
            {"message": "Je hebt geen rechten voor MKS"},
            status=status.HTTP_403_FORBIDDEN,
        )

    if isinstance(exc, InvalidTokenError):
        return Response(
            {"message": "Unauthorized"},
            status=status.HTTP_403_FORBIDDEN,
        )
    if isinstance(exc, DistrictNotFoundError):
        return Response(
            {"message": "Het stadsdeel voor dit adres is niet gevonden"},
            status=status.HTTP_404_NOT_FOUND,
        )

    if isinstance(exc, RedisTimeoutError):
        return Response(
            {
                "message": "Taken kunnen momenteel niet worden afgerond! Probeer het later nog eens."
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    if response is not None:
        response.data["status_code"] = response.status_code

    return response
