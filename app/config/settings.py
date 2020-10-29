import os
from datetime import timedelta
from os.path import join

import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY")

ENVIRONMENT = os.getenv("ENVIRONMENT")
DEBUG = ENVIRONMENT == "development"

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"

# TODO: Configure this in the environment variables
# ALLOWED_HOSTS = (
#     "0.0.0.0",
#     "localhost",
#     "zaak-gateway",
#     "acc.looplijst.top.amsterdam.nl",
# )
ALLOWED_HOSTS = "*"
# TODO: Configure this in the environment variables
CORS_ORIGIN_WHITELIST = ("http://0.0.0.0:2999", "http://localhost:2999")
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
    "django_filters",
    # Apps
    "apps.users",
    "apps.cases",
    "apps.debriefings",
    "apps.permits",
    "apps.fines",
    "apps.addresses",
    "apps.visits",
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
    "DEFAULT_FILTER_BACKENDS": ["django_filters.rest_framework.DjangoFilterBackend"],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "PAGE_SIZE": 100,
    "DATETIME_FORMAT": "%Y-%m-%dT%H:%M:%S%z",
    "DEFAULT_RENDERER_CLASSES": (
        "rest_framework.renderers.JSONRenderer",
        "rest_framework.renderers.BrowsableAPIRenderer",
    ),
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
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

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {"class": "logging.StreamHandler", "level": "DEBUG"},
    },
    "loggers": {
        "apps": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": True,
        },
        "mozilla_django_oidc": {"handlers": ["console"], "level": "DEBUG"},
    },
}

OIDC_RP_CLIENT_ID = os.environ.get("OIDC_RP_CLIENT_ID")
OIDC_RP_CLIENT_SECRET = os.environ.get("OIDC_RP_CLIENT_SECRET")
OIDC_USERNAME_ALGO = "apps.users.utils.generate_username"
OIDC_RP_SIGN_ALGO = "RS256"
OIDC_RP_SCOPES = "openid"
OIDC_VERIFY_SSL = True
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
ACCEPTANCE_OIDC_REDIRECT_URL = "https://acc.top.amsterdam.nl/authentication/callback"
PRODUCTION_OIDC_REDIRECT_URL = "https://top.amsterdam.nl/authentication/callback"

OIDC_REDIRECT_URL = ACCEPTANCE_OIDC_REDIRECT_URL

if ENVIRONMENT == "production":
    OIDC_REDIRECT_URL = PRODUCTION_OIDC_REDIRECT_URL


LOCAL_DEVELOPMENT_AUTHENTICATION = (
    os.getenv("LOCAL_DEVELOPMENT_AUTHENTICATION", False) == "True"
)

AUTH_USER_MODEL = "users.User"

AUTHENTICATION_BACKENDS = (
    "django.contrib.auth.backends.ModelBackend",
    "apps.users.auth.AuthenticationBackend",
)


SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(hours=4),
    # We don't refresh tokens yet, so we set refresh lifetime to zero
    "REFRESH_TOKEN_LIFETIME": timedelta(seconds=0),
}


# BAG Access request settings
BAG_API_SEARCH_URL = os.getenv(
    "BAG_API_SEARCH_URL", "https://api.data.amsterdam.nl/atlas/search/adres/"
)
BELASTING_API_URL = os.getenv(
    "BELASTING_API_URL",
    "https://api-acc.belastingen.centric.eu/bel/inn/afne/vora/v1/vorderingenidentificatienummer/",
)
BELASTING_API_ACCESS_TOKEN = os.getenv("BELASTING_API_ACCESS_TOKEN", None)

# Secret keys which can be used to access certain parts of the API
SECRET_KEY_TOP_ZAKEN = os.getenv("SECRET_KEY_TOP_ZAKEN", None)

# Settings to improve security
is_secure_environment = False if ENVIRONMENT == "development" else True
# NOTE: this is commented out because currently the internal health check is done over HTTP
# SECURE_SSL_REDIRECT = is_secure_environment
SESSION_COOKIE_SECURE = is_secure_environment
CSRF_COOKIE_SECURE = is_secure_environment
DEBUG = not is_secure_environment
SECURE_HSTS_SECONDS = 60
SECURE_HSTS_INCLUDE_SUBDOMAINS = is_secure_environment
SECURE_HSTS_PRELOAD = is_secure_environment
X_FRAME_OPTIONS = "DENY"
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True

DECOS_JOIN_USERNAME = os.getenv("DECOS_JOIN_USERNAME", None)
DECOS_JOIN_PASSWORD = os.getenv("DECOS_JOIN_PASSWORD", None)
DECOS_JOIN_PASSWORD_PROD = os.getenv("DECOS_JOIN_PASSWORD_PROD", None)
DECOS_JOIN_API = "https://decosdvl.acc.amsterdam.nl:443/decosweb/aspx/api/v1/"
DECOS_JOIN_BANDB_ID = "D8D961993D7E478D9B644587822817B1"
DECOS_JOIN_VAKANTIEVERHUUR_ID = "TBD"
DECOS_JOIN_BOOK_KNOWN_BAG_OBJECTS = "90642DCCC2DB46469657C3D0DF0B1ED7"
DECOS_JOIN_BOOK_UNKNOWN_BOOK = "B1FF791EA9FA44698D5ABBB1963B94EC"
USE_DECOS_MOCK_DATA = True
