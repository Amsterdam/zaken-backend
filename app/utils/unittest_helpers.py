from apps.users.models import User
from django.conf import settings
from django.contrib.auth.models import Group
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

AUTHENTICATED_CLIENT_EMAIL = "f.foo@foo.com"


def add_user_to_authorized_groups(user):
    """
    Adds users to the authorized groups configured in the OIDC_AUTHORIZED_GROUPS
    """
    realm_access_groups = settings.OIDC_AUTHORIZED_GROUPS

    for realm_access_group in realm_access_groups:
        group, _ = Group.objects.get_or_create(name=realm_access_group)
        group.user_set.add(user)
    pass


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
    add_user_to_authorized_groups(user)
    access_token = RefreshToken.for_user(user).access_token

    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION="Bearer {}".format(access_token))
    return client


def get_unauthenticated_client():
    """
    Returns an unauthenticated APIClient, for unit testing API requests
    """
    return APIClient()
