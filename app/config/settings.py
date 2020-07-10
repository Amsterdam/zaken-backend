# NOTE: Development settings
import os
from os.path import join

import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY")
DEBUG = os.environ.get("DJANGO_DEBUG", False)
ROOT_URLCONF = "config.urls"
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

WSGI_APPLICATION = "config.wsgi.application"

# TODO: Configure this in the environment variables
ALLOWED_HOSTS = (
    "0.0.0.0",
    "localhost",
    "zaak-gateway",
    "acc.looplijst.top.amsterdam.nl",
)
CORS_ORIGIN_WHITELIST = (
    "http://0.0.0.0:3000",
    "http://localhost:3000",
    "http://0.0.0.0:3001",
    "http://localhost:3001",
)
CORS_ORIGIN_ALLOW_ALL = False

INSTALLED_APPS = (
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "corsheaders",
    # Third party apps
    "mozilla_django_oidc",
    "rest_framework",
    "drf_spectacular",
    "django_extensions",
    # Apps
    "apps.users",
)

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("DATABASE_NAME"),
        "USER": os.environ.get("DATABASE_USER"),
        "PASSWORD": os.environ.get("DATABASE_PASSWORD"),
        "HOST": os.environ.get("DATABASE_HOST"),
        "PORT": os.environ.get("DATABASE_PORT"),
    },
}

MIDDLEWARE = (
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "mozilla_django_oidc.middleware.SessionRefresh",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
)

STATIC_URL = "/static/"
STATIC_ROOT = os.path.normpath(join(os.path.dirname(BASE_DIR), "static"))

MEDIA_URL = "/media/"
MEDIA_ROOT = os.path.normpath(join(os.path.dirname(BASE_DIR), "media"))

STATICFILES_FINDERS = (
    "django.contrib.staticfiles.finders.FileSystemFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
)

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

REST_FRAMEWORK = {
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "PAGE_SIZE": 100,
    "DATETIME_FORMAT": "%Y-%m-%dT%H:%M:%S%z",
    "DEFAULT_RENDERER_CLASSES": (
        "rest_framework.renderers.JSONRenderer",
        "rest_framework.renderers.BrowsableAPIRenderer",
    ),
}

SPECTACULAR_SETTINGS = {
    "SCHEMA_PATH_PREFIX": "/api/v[0-9]/",
    "TITLE": "Zaken Backend Gateway API",
    "VERSION": "v1",
}

# Error logging through Sentry
sentry_sdk.init(
    dsn=os.environ.get("SENTRY_DSN", ""), integrations=[DjangoIntegration()]
)

OIDC_RP_CLIENT_ID = os.environ.get("OIDC_RP_CLIENT_ID")
OIDC_RP_CLIENT_SECRET = os.environ.get("OIDC_RP_CLIENT_SECRET")
OIDC_USERNAME_ALGO = "api.users.utils.generate_username"

ACCEPTANCE_OIDC_REDIRECT_URL = "https://acc.top.amsterdam.nl/authentication/callback"
PRODUCTION_OIDC_REDIRECT_URL = "https://top.amsterdam.nl/authentication/callback"

OIDC_REDIRECT_URL = ACCEPTANCE_OIDC_REDIRECT_URL

if ENVIRONMENT == "production":
    OIDC_REDIRECT_URL = PRODUCTION_OIDC_REDIRECT_URL

OIDC_RP_SIGN_ALGO = "RS256"

OIDC_RP_SCOPES = "openid"

OIDC_VERIFY_SSL = True

# https://auth.grip-on-it.com/v2/rjsfm52t/oidc/idp/.well-known/openid-configuration
OIDC_OP_AUTHORIZATION_ENDPOINT = os.getenv(
    "OIDC_OP_AUTHORIZATION_ENDPOINT",
    "https://auth.grip-on-it.com/v2/rjsfm52t/oidc/idp/authorize",
)
OIDC_OP_TOKEN_ENDPOINT = os.getenv(
    "OIDC_OP_TOKEN_ENDPOINT", "https://auth.grip-on-it.com/v2/rjsfm52t/oidc/idp/token"
)
OIDC_OP_USER_ENDPOINT = os.getenv(
    "OIDC_OP_USER_ENDPOINT", "https://auth.grip-on-it.com/v2/rjsfm52t/oidc/idp/userinfo"
)
OIDC_OP_JWKS_ENDPOINT = os.getenv(
    "OIDC_OP_JWKS_ENDPOINT",
    "https://auth.grip-on-it.com/v2/rjsfm52t/oidc/idp/.well-known/jwks.json",
)

OIDC_USE_NONCE = True

LOCAL_DEVELOPMENT_AUTHENTICATION = (
    os.getenv("LOCAL_DEVELOPMENT_AUTHENTICATION", False) == "True"
)

AUTH_USER_MODEL = "users.User"

AUTHENTICATION_BACKENDS = (
    "django.contrib.auth.backends.ModelBackend",
    "apps.users.auth.AuthenticationBackend",
)

REST_FRAMEWORK = {
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "PAGE_SIZE": 100,
    "DATETIME_FORMAT": "%Y-%m-%dT%H:%M:%S%z",
    "DEFAULT_RENDERER_CLASSES": (
        "rest_framework.renderers.JSONRenderer",
        "rest_framework.renderers.BrowsableAPIRenderer",
    ),
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated"],
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
}
