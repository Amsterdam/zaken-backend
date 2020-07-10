from django.conf import settings

from .auth_dev import DevelopmentAuthenticationBackend
from .auth_grip import OIDCAuthenticationBackend

if settings.LOCAL_DEVELOPMENT_AUTHENTICATION:
    AuthenticationBackend = DevelopmentAuthenticationBackend
else:
    AuthenticationBackend = OIDCAuthenticationBackend
