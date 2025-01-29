import logging
import time

from django.conf import settings
from django.core.exceptions import PermissionDenied
from drf_spectacular.contrib.rest_framework_simplejwt import SimpleJWTScheme
from mozilla_django_oidc.auth import OIDCAuthenticationBackend
from mozilla_django_oidc.contrib.drf import OIDCAuthentication
from rest_framework_simplejwt.authentication import JWTAuthentication

from .auth_dev import DevelopmentAuthenticationBackend


class OIDCAuthenticationBackend(OIDCAuthenticationBackend):
    def save_user(self, user, claims):
        user.first_name = claims.get("given_name", "")
        user.last_name = claims.get("family_name", "")
        user.save()
        return user

    def create_user(self, claims):
        user = super(OIDCAuthenticationBackend, self).create_user(claims)
        user = self.save_user(user, claims)
        return user

    def update_user(self, user, claims):
        user = self.save_user(user, claims)
        return user

    def validate_issuer(self, payload):
        issuer = self.get_settings("OIDC_OP_ISSUER")
        if not issuer == payload["iss"]:
            raise PermissionDenied(
                '"iss": %r does not match configured value for OIDC_OP_ISSUER: %r'
                % (payload["iss"], issuer)
            )

    def validate_audience(self, payload):
        trusted_audiences = self.get_settings("OIDC_TRUSTED_AUDIENCES", [])
        trusted_audiences = set(trusted_audiences)
        audience = payload["aud"]
        audience = set(audience)
        distrusted_audiences = audience.difference(trusted_audiences)
        if distrusted_audiences:
            raise PermissionDenied(
                '"aud" contains distrusted audiences: %r' % distrusted_audiences
            )

    def validate_expiry(self, payload):
        expire_time = payload["exp"]
        now = time.time()
        if now > expire_time:
            raise PermissionDenied(
                "Access-token is expired %r > %r" % (now, expire_time)
            )

    def validate_access_token(self, payload):
        self.validate_issuer(payload)
        self.validate_audience(payload)
        self.validate_expiry(payload)
        return payload

    def get_userinfo(self, access_token, id_token=None, payload=None):
        userinfo = self.verify_token(access_token)
        self.validate_access_token(userinfo)
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
