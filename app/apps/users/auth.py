from django.conf import settings
from drf_spectacular.contrib.rest_framework_simplejwt import SimpleJWTScheme
from mozilla_django_oidc.contrib.drf import OIDCAuthentication
from rest_framework_simplejwt.authentication import JWTAuthentication

from .auth_dev import DevelopmentAuthenticationBackend
from .auth_keycloak import OIDCAuthenticationBackend

if settings.LOCAL_DEVELOPMENT_AUTHENTICATION:
    AuthenticationBackend = DevelopmentAuthenticationBackend
    AuthenticationClass = JWTAuthentication
else:
    AuthenticationBackend = OIDCAuthenticationBackend
    AuthenticationClass = OIDCAuthentication


class OIDCScheme(SimpleJWTScheme):
    target_class = "mozilla_django_oidc.contrib.drf.OIDCAuthentication"
    name = "Authenticate"
