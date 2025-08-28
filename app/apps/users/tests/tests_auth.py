"""
TODO: These are mostly tests for getting an access token through the oidc-authenticate url.
this authentication is somewhat deprecated, but can still be used for local development
authentication in which this project servers as its own authentication provider.

We are using an implicit autentication flow with a dedicated authentication provider/server now.
Additional tests for user creation/update and role verification on authenticated requests are needed.
"""

from unittest.mock import Mock

from django.core.exceptions import SuspiciousOperation
from django.test import TestCase
from mozilla_django_oidc.contrib.drf import OIDCAuthenticationBackend

from app.utils.unittest_helpers import get_test_user

MOCK_AUTH_CODE = "FOO_CODE"
MOCK_AUTH_REQUEST = Mock()
MOCK_AUTH_REQUEST.data = Mock()
MOCK_AUTH_REQUEST.data.code = MOCK_AUTH_CODE
MOCK_AUTH_REQUEST.META = {}
MOCK_AUTH_REQUEST.META["HTTP_REFERER"] = "FOO REDIRECT"


class AuthTest(TestCase):
    def test_no_code_in_request(self):
        """
        An authentication without given data and access code will not do anything
        """

        authentication_backend = OIDCAuthenticationBackend()

        authentication_backend.get_token = Mock()
        authentication_backend.verify_token = Mock()
        authentication_backend.store_tokens = Mock()
        authentication_backend.get_or_create_user = Mock()

        request = {}
        result = authentication_backend.authenticate(request)

        self.assertIsNone(result)
        authentication_backend.get_token.assert_not_called()
        authentication_backend.verify_token.assert_not_called()
        authentication_backend.store_tokens.assert_not_called()
        authentication_backend.get_or_create_user.assert_not_called()

    def test_user_created(self):
        """
        An succesful authentication should create a new user
        """
        authentication_backend = OIDCAuthenticationBackend()

        authentication_backend.get_token = Mock()
        authentication_backend.store_tokens = Mock()

        # Mock verify token and payload
        authentication_backend.verify_token = Mock()
        authentication_backend.verify_token.return_value = {"payload_foo": "foo_data"}

        # Mock user creation
        FOO_USER = get_test_user()
        authentication_backend.get_or_create_user = Mock()
        authentication_backend.get_or_create_user.return_value = FOO_USER

        authenticated_result = authentication_backend.authenticate(MOCK_AUTH_REQUEST)

        authentication_backend.get_token.assert_called_once()
        authentication_backend.verify_token.assert_called_once()
        authentication_backend.store_tokens.assert_called_once()

        # Most importantly, the get_or_create_user function is called, and it's return value is given
        authentication_backend.get_or_create_user.assert_called_once()
        self.assertEqual(authenticated_result, FOO_USER)

    def test_verification_fails(self):
        """
        No user is created if token verification fails
        """
        authentication_backend = OIDCAuthenticationBackend()

        authentication_backend.get_token = Mock()
        authentication_backend.store_tokens = Mock()
        authentication_backend.get_or_create_user = Mock()

        # Mock verify token and payload
        # This mock raises an 'SuspiciousOperation' exception
        authentication_backend.verify_token = Mock(
            side_effect=SuspiciousOperation("Token not verified")
        )

        # Call the authentication
        with self.assertRaises(Exception):
            authentication_backend.authenticate(MOCK_AUTH_REQUEST)

        # Verify is called
        authentication_backend.verify_token.assert_called_once()

        # But the user creation not
        authentication_backend.get_or_create_user.assert_not_called()
