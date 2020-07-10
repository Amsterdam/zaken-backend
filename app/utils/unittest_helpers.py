from apps.users.models import User
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

AUTHENTICATED_CLIENT_EMAIL = "f.foo@foo.com"


def get_test_user():
    """
    Creates and returns a test user
    """
    return User.objects.get_or_create(email=AUTHENTICATED_CLIENT_EMAIL)[0]


def get_authenticated_client():
    """
    Returns an authenticated APIClient, for unit testing API requests
    """
    user = get_test_user()
    access_token = RefreshToken.for_user(user).access_token

    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION="Bearer {}".format(access_token))
    return client


def get_unauthenticated_client():
    """
    Returns an unauthenticated APIClient, for unit testing API requests
    """
    return APIClient()
