import os
from datetime import timedelta
from os.path import join

import sentry_sdk
from celery.schedules import crontab
from keycloak_oidc.default_settings import *  # noqa
from sentry_sdk.integrations.django import DjangoIntegration

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY")

ENVIRONMENT = os.getenv("ENVIRONMENT")
DEBUG = ENVIRONMENT == "development"

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"

USE_TZ = True
TIME_ZONE = "Europe/Amsterdam"

ZAKEN_CONTAINER_HOST = os.getenv("ZAKEN_CONTAINER_HOST")

ALLOWED_HOSTS = "*"

# TODO: Configure this in the environment variables
CORS_ORIGIN_WHITELIST = (
    "https://wonen.zaken.amsterdam.nl",
    "https://acc.wonen.zaken.amsterdam.nl",
    "http://0.0.0.0:2999",
    "http://localhost:2999",
)
CORS_ORIGIN_ALLOW_ALL = False

INSTALLED_APPS = (
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.postgres",
    "corsheaders",
    # Third party apps
    "keycloak_oidc",
    "rest_framework",
    "drf_spectacular",
    "django_extensions",
    "django_filters",
    "django_spaghetti",
    "django_celery_beat",
    "django_celery_results",
    "zgw_consumers",
    "axes",
    # Health checks. (Expand when more services become available)
    "health_check",
    "health_check.db",
    "health_check.contrib.migrations",
    "health_check.contrib.rabbitmq",
    "health_check.contrib.celery_ping",
    # Apps
    "apps.users",
    "apps.cases",
    "apps.decisions",
    "apps.debriefings",
    "apps.permits",
    "apps.fines",
    "apps.addresses",
    "apps.visits",
    "apps.events",
    "apps.health",
    "apps.support",
    "apps.camunda",
    "apps.openzaak",
    "apps.summons",
    "apps.schedules",
)

# Add apps here to make them appear in the graphing visualisation
SPAGHETTI_SAUCE = {
    "apps": [
        "users",
        "cases",
        "debriefings",
        "permits",
        "fines",
        "addresses",
        "visits",
        "events",
        "summons",
        "camunda",
        "decisions",
        "schedules",
    ],
    "show_fields": False,
}

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
    "django_permissions_policy.PermissionsPolicyMiddleware",
    "csp.middleware.CSPMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "mozilla_django_oidc.middleware.SessionRefresh",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "axes.middleware.AxesMiddleware",
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
    "DEFAULT_PERMISSION_CLASSES": [
        "keycloak_oidc.drf.permissions.IsInAuthorizedRealm",
    ],
    "DEFAULT_AUTHENTICATION_CLASSES": ("apps.users.auth.AuthenticationClass",),
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

"""
TODO: Only a few of these settings are actually used for our current flow,
but the mozilla_django_oidc OIDCAuthenticationBackend required these to be set.
Since we are already subclassing from OIDCAuthenticationBackend, we can overwrite the requirements and cleanup these settings.

The following fields are used:
OIDC_USERNAME_ALGO
OIDC_RP_SIGN_ALGO
OIDC_USE_NONCE
OIDC_AUTHORIZED_GROUPS
OIDC_OP_USER_ENDPOINT
"""
OIDC_RP_CLIENT_ID = os.environ.get("OIDC_RP_CLIENT_ID", None)
OIDC_RP_CLIENT_SECRET = os.environ.get("OIDC_RP_CLIENT_SECRET", None)
OIDC_USE_NONCE = False
OIDC_AUTHORIZED_GROUPS = ("wonen_zaaksysteem", "wonen_zaak")
OIDC_AUTHENTICATION_CALLBACK_URL = "oidc-authenticate"

OIDC_OP_AUTHORIZATION_ENDPOINT = os.getenv(
    "OIDC_OP_AUTHORIZATION_ENDPOINT",
    "https://iam.amsterdam.nl/auth/realms/datapunt-ad-acc/protocol/openid-connect/auth",
)
OIDC_OP_TOKEN_ENDPOINT = os.getenv(
    "OIDC_OP_TOKEN_ENDPOINT",
    "https://iam.amsterdam.nl/auth/realms/datapunt-ad-acc/protocol/openid-connect/token",
)
OIDC_OP_USER_ENDPOINT = os.getenv(
    "OIDC_OP_USER_ENDPOINT",
    "https://iam.amsterdam.nl/auth/realms/datapunt-ad-acc/protocol/openid-connect/userinfo",
)
OIDC_OP_JWKS_ENDPOINT = os.getenv(
    "OIDC_OP_JWKS_ENDPOINT",
    "https://iam.amsterdam.nl/auth/realms/datapunt-ad-acc/protocol/openid-connect/certs",
)
OIDC_OP_LOGOUT_ENDPOINT = os.getenv(
    "OIDC_OP_LOGOUT_ENDPOINT",
    "https://iam.amsterdam.nl/auth/realms/datapunt-ad-acc/protocol/openid-connect/logout",
)

LOCAL_DEVELOPMENT_AUTHENTICATION = (
    os.getenv("LOCAL_DEVELOPMENT_AUTHENTICATION", False) == "True"
)

SESSION_COOKIE_AGE = 60 * 5
SESSION_SAVE_EVERY_REQUEST = True

AUTH_USER_MODEL = "users.User"

AUTHENTICATION_BACKENDS = (
    "axes.backends.AxesBackend",
    "django.contrib.auth.backends.ModelBackend",
    "apps.users.auth.AuthenticationBackend",
)


# Simple JWT is used for local development authentication only.
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(hours=120),
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
CAMUNDA_SECRET_KEY = os.getenv("CAMUNDA_SECRET_KEY")
# Authentication for the rest calls to camunda
CAMUNDA_REST_AUTH = os.getenv("CAMUNDA_REST_AUTH")


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

# Settings for Permissions-Policy header
PERMISSIONS_POLICY = {
    "accelerometer": [],
    "ambient-light-sensor": [],
    "autoplay": [],
    "camera": [],
    "display-capture": [],
    "document-domain": [],
    "encrypted-media": [],
    "fullscreen": [],
    "geolocation": [],
    "gyroscope": [],
    "interest-cohort": [],
    "magnetometer": [],
    "microphone": [],
    "midi": [],
    "payment": [],
    "usb": [],
}

# Settings for Content-Security-Policy header
CSP_DEFAULT = ("'self'", "unpkg.com")
CSP_DEFAULT_UNSAFE_INLINE = ("'unsafe-inline'", "'self'", "unpkg.com")
CSP_DEFAULT_SRC = CSP_DEFAULT
CSP_FRAME_ANCESTORS = ("'self'",)
CSP_SCRIPT_SRC = CSP_DEFAULT_UNSAFE_INLINE
CSP_IMG_SRC = CSP_DEFAULT
CSP_STYLE_SRC = CSP_DEFAULT_UNSAFE_INLINE
CSP_CONNECT_SRC = CSP_DEFAULT

# DECOS_ENABLED = False
DECOS_JOIN_AUTH_BASE64 = os.getenv("DECOS_JOIN_AUTH_BASE64", None)
DECOS_JOIN_API = os.getenv(
    "DECOS_JOIN_API", "https://decosdvl.acc.amsterdam.nl/decosweb/aspx/api/v1/"
)
DECOS_JOIN_AUTH_BASE64 = os.getenv("DECOS_JOIN_AUTH_BASE64", None)

# Decos Join Book keys
DECOS_JOIN_B_EN_B_VERGUNNING_ID = "D8D961993D7E478D9B644587822817B1"
DECOS_JOIN_VAKANTIEVERHUURVERGUNNING_ID = "1C0D0EBF55EE49EE872AE1D61433DC21"
DECOS_JOIN_VAKANTIEVERHUUR_MELDINGEN_ID = "E6325A942DF440B386D8DFFEC013F795"
DECOS_JOIN_VAKANTIEVERHUUR_AFMELDINGEN_ID = "F86015A1A927451082A9E2F2023EF8F7"
DECOS_JOIN_OMZETTINGSVERGUNNING_ID = "82A3A125E688446E987F3C477CC88315"
DECOS_JOIN_SPLITSINGSVERGUNNING_ID = "1EBF2890290D4A07BC8A79B450F3E2DA"
DECOS_JOIN_ONTREKKING_VORMING_SAMENVOEGING_VERGUNNINGEN_ID = (
    "DD0616BFE4AE45539C2FF95D6A55ED82"
)
DECOS_JOIN_LIGPLAATSVERGUNNING_ID = "7C9DAAA30DBF4B06A68B555D09CEC6E4"
DECOS_JOIN_DEFAULT_PERMIT_VALID_CONF = (
    (
        DECOS_JOIN_B_EN_B_VERGUNNING_ID,
        "B&B - vergunning",
    ),
    (
        DECOS_JOIN_VAKANTIEVERHUURVERGUNNING_ID,
        "Vakantieverhuurvergunning",
    ),
    (
        DECOS_JOIN_OMZETTINGSVERGUNNING_ID,
        "Omzettingsvergunning",
    ),
    (
        DECOS_JOIN_SPLITSINGSVERGUNNING_ID,
        "Splitsingsvergunning",
    ),
    (
        DECOS_JOIN_ONTREKKING_VORMING_SAMENVOEGING_VERGUNNINGEN_ID,
        "Onttrekking- vorming en samenvoegingsvergunning",
    ),
    (
        DECOS_JOIN_LIGPLAATSVERGUNNING_ID,
        "Ligplaatsvergunning",
    ),
)
DECOS_JOIN_DEFAULT_PERMIT_VALID_EXPRESSION = "{date6} <= {ts_now} and {date7} >= {ts_now} and {date5} <= {ts_now} and '{dfunction}'.startswith('Verleend') or {date6} <= {ts_now} and {date5} <= {ts_now} and '{dfunction}'.startswith('Verleend')"
DECOS_JOIN_DEFAULT_PERMIT_VALID_INITIAL_DATA = {
    "date5": 0,
    "date6": 0,
    "date7": 9999999999,
    "date13": 9999999999,
    "dfunction": "",
}
DECOS_JOIN_DEFAULT_FIELD_MAPPING = {
    "date6": "DATE_VALID_FROM",
    "date7": "DATE_VALID_UNTIL",
    "dfunction": "RESULT",
    "text45": "PERMIT_NAME",
    "text9": "PERMIT_TYPE",
    "surname": "APPLICANT",
    "text19": "HOLDER",
    "subject1": "SUBJECT",
    "text6": "ADDRESS",
}
DECOS_JOIN_BOOK_UNKNOWN_BOOK = "B1FF791EA9FA44698D5ABBB1963B94EC"
DECOS_JOIN_BOOK_KNOWN_BAG_OBJECTS = "90642DCCC2DB46469657C3D0DF0B1ED7"
USE_DECOS_MOCK_DATA = os.getenv("USE_DECOS_MOCK_DATA", False) == "True"


RABBIT_MQ_URL = os.getenv("RABBIT_MQ_URL")
RABBIT_MQ_USERNAME = os.getenv("RABBIT_MQ_USERNAME")
RABBIT_MQ_PASSWORD = os.getenv("RABBIT_MQ_PASSWORD")

CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 30 * 60
CELERY_BROKER_URL = f"amqp://{RABBIT_MQ_USERNAME}:{RABBIT_MQ_PASSWORD}@{RABBIT_MQ_URL}"

BROKER_URL = CELERY_BROKER_URL
CELERY_RESULT_BACKEND = "django-db"
CELERY_BEAT_SCHEDULE = {
    "queue_every_five_mins": {
        "task": "apps.health.tasks.query_every_five_mins",
        "schedule": crontab(minute=5),
    },
}

CAMUNDA_HEALTH_CHECK_URL = os.getenv("CAMUNDA_HEALTH_CHECK_URL")
CAMUNDA_REST_URL = os.getenv("CAMUNDA_REST_URL", "http://camunda:8080/engine-rest/")
CAMUNDA_PROCESS_VISIT = "zaak_wonen_visit"
CAMUNDA_PROCESS_SUMMON = "zaak_wonen_summon"
CAMUNDA_PROCESS_DECISION = "zaak_wonen_decision"

REDIS = os.getenv("REDIS")
REDIS_URL = f"redis://{REDIS}"
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": REDIS_URL,
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        },
    }
}

LOGOUT_REDIRECT_URL = "/admin"

DEFAULT_THEME = os.getenv("DEFAULT_THEME", "Vakantieverhuur")
DEFAULT_REASON = os.getenv("DEFAULT_REASON", "Melding")

DEFAULT_SCHEDULE_ACTIONS = os.getenv("DEFAULT_SCHEDULE_ACTIONS").split(",")
DEFAULT_SCHEDULE_WEEK_SEGMENTS = os.getenv("DEFAULT_SCHEDULE_WEEK_SEGMENTS").split(",")
DEFAULT_SCHEDULE_DAY_SEGMENTS = os.getenv("DEFAULT_SCHEDULE_DAY_SEGMENTS").split(",")
DEFAULT_SCHEDULE_HIGH_PRIORITY = os.getenv("DEFAULT_SCHEDULE_HIGH_PRIORITY")
DEFAULT_SCHEDULE_NORMAL_PRIORITY = os.getenv("DEFAULT_SCHEDULE_NORMAL_PRIORITY")

# ZGW_CONSUMERS_OAS_CACHE = django_redis.cache.RedisCache

LOGOUT_REDIRECT_URL = "/admin"


OPEN_ZAAK_CONTAINER_HOST = os.getenv("OPEN_ZAAK_CONTAINER_HOST", None)
OPEN_ZAAK_PORT = os.getenv("OPEN_ZAAK_PORT", None)
OPEN_ZAAK_HOST = (
    f"http://{OPEN_ZAAK_CONTAINER_HOST}:{OPEN_ZAAK_PORT}"
    if OPEN_ZAAK_PORT
    else f"https://{OPEN_ZAAK_CONTAINER_HOST}"
)

OPEN_ZAAK_CLIENT = os.getenv("OPEN_ZAAK_CLIENT")
OPEN_ZAAK_SECRET_KEY = os.getenv("OPEN_ZAAK_SECRET_KEY")
OPEN_ZAAK_API_VERSION = os.getenv("OPEN_ZAAK_API_VERSION", "v1")
DEFAULT_CATALOGUS_RSIN = os.getenv("DEFAULT_CATALOGUS_RSIN", "002564440")
DEFAULT_CATALOGUS = os.getenv("DEFAULT_CATALOGUS")


VAKANTIEVERHUUR_REGISTRATIE_API_URL = os.getenv("VAKANTIEVERHUUR_REGISTRATIE_API_URL")
VAKANTIEVERHUUR_REGISTRATIE_API_ACCESS_TOKEN = os.getenv(
    "VAKANTIEVERHUUR_REGISTRATIE_API_ACCESS_TOKEN"
)
VAKANTIEVERHUUR_REGISTRATIE_API_HEALTH_CHECK_BSN = os.getenv(
    "VAKANTIEVERHUUR_REGISTRATIE_API_HEALTH_CHECK_BSN"
)
VAKANTIEVERHUUR_REGISTRATIE_API_HEALTH_CHECK_BAG_ID = os.getenv(
    "VAKANTIEVERHUUR_REGISTRATIE_API_HEALTH_CHECK_BAG_ID"
)
VAKANTIEVERHUUR_REGISTRATIE_API_HEALTH_CHECK_REGISTRATION_NUMBER = os.getenv(
    "VAKANTIEVERHUUR_REGISTRATIE_API_HEALTH_CHECK_REGISTRATION_NUMBER"
)
