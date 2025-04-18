from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

AUTHENTICATED_CLIENT_EMAIL = "f.foo@foo.com"


def add_user_to_authorized_groups(user):
    """
    Adds users to the authorized groups configured in the OIDC_AUTHORIZED_GROUPS
    """
    realm_access_groups = "all_permissions"
    all_permissions = Permission.objects.all()
    for realm_access_group in realm_access_groups:
        group, _ = Group.objects.get_or_create(name=realm_access_group)
        for permission in all_permissions:
            group.permissions.add(permission)
        group.user_set.add(user)


def get_test_user():
    """
    Creates and returns a test user
    """
    return get_user_model().objects.get_or_create(email=AUTHENTICATED_CLIENT_EMAIL)[0]


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


def get_authenticated_with_token_client(access_token):
    """
    Some endpoints can be accessed using a special designated token. This creates a client for such an authenticated request.
    """
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION="{}".format(access_token))
    return client


def get_unauthenticated_client():
    """
    Returns an unauthenticated APIClient, for unit testing API requests
    """
    return APIClient()
