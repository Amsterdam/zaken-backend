import logging
import time

from django.conf import settings
from drf_spectacular.contrib.rest_framework_simplejwt import SimpleJWTScheme
from mozilla_django_oidc.auth import OIDCAuthenticationBackend
from mozilla_django_oidc.contrib.drf import OIDCAuthentication
from rest_framework_simplejwt.authentication import JWTAuthentication

from .auth_dev import DevelopmentAuthenticationBackend


class OIDCAuthenticationBackend(OIDCAuthenticationBackend):
    def validate_issuer(self, payload):
        issuer = self.get_settings("OIDC_OP_ISSUER")
        if not issuer == payload["iss"]:
            raise Exception(
                '"iss": %r does not match configured value for OIDC_OP_ISSUER: %r'
                % (payload["iss"], issuer)
            )

    def validate_audience(self, payload):
        client_id = self.get_settings("OIDC_RP_CLIENT_ID")
        trusted_audiences = self.get_settings("OIDC_TRUSTED_AUDIENCES", [])
        trusted_audiences = set(trusted_audiences)
        trusted_audiences.add(client_id)

        audience = payload["aud"]
        if not isinstance(audience, list):
            audience = [audience]
        audience = set(audience)
        distrusted_audiences = audience.difference(trusted_audiences)
        if distrusted_audiences:
            raise Exception(
                '"aud" contains distrusted audiences: %r' % distrusted_audiences
            )

    def validate_expiry(self, payload):
        expire_time = payload["exp"]
        now = time.time()
        if now > expire_time:
            raise Exception("Id-token is expired %r > %r" % (now, expire_time))

    def validate_id_token(self, payload):
        """Validate the content of the id token as required by OpenID Connect 1.0

        This aims to fulfill point 2. 3. and 9. under section 3.1.3.7. ID Token
        Validation
        """
        self.validate_issuer(payload)
        self.validate_audience(payload)
        self.validate_expiry(payload)
        return payload

    def get_userinfo(self, access_token, id_token=None, payload=None):
        """
        Get user info from the OIDC provider.
        """
        userinfo = self.verify_token(access_token)
        self.validate_id_token(userinfo)
        return userinfo


LOGGER = logging.getLogger(__name__)

if settings.LOCAL_DEVELOPMENT_AUTHENTICATION:
    AuthenticationBackend = DevelopmentAuthenticationBackend
    AuthenticationClass = JWTAuthentication
else:
    AuthenticationBackend = OIDCAuthenticationBackend
    AuthenticationClass = OIDCAuthentication


class OIDCScheme(SimpleJWTScheme):
    target_class = "mozilla_django_oidc.contrib.drf.OIDCAuthentication"
    name = "Authenticate"
