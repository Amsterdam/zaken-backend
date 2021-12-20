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

# Settings to improve security
is_secure_environment = not DEBUG

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
    "rest_framework.authtoken",
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
    "apps.summons",
    "apps.schedules",
    "apps.workflow",
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
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.LimitOffsetPagination",
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "PAGE_SIZE": 500,
    "DATETIME_FORMAT": "%Y-%m-%dT%H:%M:%S%z",
    "DEFAULT_RENDERER_CLASSES": (
        "rest_framework.renderers.JSONRenderer",
        "rest_framework.renderers.BrowsableAPIRenderer",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "keycloak_oidc.drf.permissions.IsInAuthorizedRealm",
    ),
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "apps.users.auth.AuthenticationClass",
        "rest_framework.authentication.TokenAuthentication",
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
        "utils": {
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
OIDC_AUTHORIZED_GROUPS = (
    "wonen_zaaksysteem",
    "wonen_zaak",
    "enable_persistent_token",
)
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

DATA_UPLOAD_MAX_MEMORY_SIZE = 5242880

SESSION_COOKIE_AGE = int(os.getenv("SESSION_COOKIE_AGE", "300"))
SESSION_SAVE_EVERY_REQUEST = True

AUTH_USER_MODEL = "users.User"

AUTHENTICATION_BACKENDS = (
    "axes.backends.AxesBackend",
    "django.contrib.auth.backends.ModelBackend",
    "apps.users.auth.AuthenticationBackend",
)

AXES_RESET_ON_SUCCESS = True
AXES_ENABLED = os.getenv("AXES_ENABLED", "True") == "True"
AXES_META_PRECEDENCE_ORDER = ["HTTP_X_FORWARDED_FOR", "REMOTE_ADDR"]

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
CSP_DEFAULT = ("'self'", "unpkg.com", "cdnjs.cloudflare.com/ajax/libs/vis/")
CSP_DEFAULT_UNSAFE_INLINE = (
    "'unsafe-inline'",
    "'self'",
    "unpkg.com",
    "cdnjs.cloudflare.com/ajax/libs/vis/",
)
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

# TOP Connection settings
SECRET_KEY_AZA_TOP = os.getenv("SECRET_KEY_AZA_TOP")
TOP_API_URL = os.getenv("TOP_API_URL")

RABBIT_MQ_URL = os.getenv("RABBIT_MQ_URL")
RABBIT_MQ_USERNAME = os.getenv("RABBIT_MQ_USERNAME")
RABBIT_MQ_PASSWORD = os.getenv("RABBIT_MQ_PASSWORD")

CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 30 * 60
CELERY_BROKER_URL = f"amqp://{RABBIT_MQ_USERNAME}:{RABBIT_MQ_PASSWORD}@{RABBIT_MQ_URL}"

BROKER_URL = CELERY_BROKER_URL
CELERY_TASK_TRACK_STARTED = True
CELERY_RESULT_BACKEND = "django-db"
CELERY_TASK_TIME_LIMIT = 30 * 60
CELERY_BEAT_SCHEDULE = {
    "queue_every_five_mins": {
        "task": "apps.health.tasks.query_every_five_mins",
        "schedule": crontab(minute=5),
    },
}

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
DEFAULT_REASON = os.getenv("DEFAULT_REASON", "SIA melding")

DEFAULT_SCHEDULE_ACTIONS = os.getenv("DEFAULT_SCHEDULE_ACTIONS").split(",")
DEFAULT_SCHEDULE_WEEK_SEGMENTS = os.getenv("DEFAULT_SCHEDULE_WEEK_SEGMENTS").split(",")
DEFAULT_SCHEDULE_DAY_SEGMENTS = os.getenv("DEFAULT_SCHEDULE_DAY_SEGMENTS").split(",")
DEFAULT_SCHEDULE_HIGH_PRIORITY = os.getenv("DEFAULT_SCHEDULE_HIGH_PRIORITY")
DEFAULT_SCHEDULE_NORMAL_PRIORITY = os.getenv("DEFAULT_SCHEDULE_NORMAL_PRIORITY")

LOGOUT_REDIRECT_URL = "/admin"

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

DEFAULT_AUTO_FIELD = "django.db.models.AutoField"


DEFAULT_WORKFLOW_TYPE = os.getenv("DEFAULT_WORKFLOW_TYPE", "director")

DEFAULT_WORKFLOW_TIMER_DURATIONS = {
    "development": timedelta(seconds=20),
    "acceptance": timedelta(seconds=240),
}

WORKFLOW_SPEC_CONFIG = {
    "default": {
        "closing_procedure": {
            "initial_data": {
                "task_monitoren_heropeningsverzoek_timer_duration": timedelta(days=92),
                "task_monitoren_nieuw_heropeningsverzoek_timer_duration": timedelta(
                    days=31
                ),
            },
            "versions": {"0.1.0": {}},
        },
        "close_case": {
            "initial_data": {},
            "versions": {
                "0.1.0": {},
            },
        },
        "decision": {
            "initial_data": {},
            "versions": {
                "0.1.0": {},
            },
        },
        "digital_surveillance": {
            "initial_data": {},
            "versions": {
                "0.1.0": {},
            },
        },
        "debrief": {
            "initial_data": {},
            "versions": {
                "0.1.0": {},
                "1.0.0": {},
                "2.0.0": {},
            },
        },
        "director": {
            "initial_data": {},
            "versions": {
                "0.2.0": {
                    "messages": {
                        "main_process": {
                            "initial_data": {
                                "status_name": DEFAULT_SCHEDULE_ACTIONS[0],
                            },
                        },
                        "aanschrijving_toevoegen": {},  # TODO Remove this
                    },
                },
                "1.0.0": {
                    "messages": {
                        "main_process": {
                            "initial_data": {
                                "status_name": DEFAULT_SCHEDULE_ACTIONS[0],
                                "authorization": {"value": "No"},
                                "reason": {"value": "default"},
                                "theme": {"value": "default"},
                            },
                        },
                        "aanschrijving_toevoegen": {},  # TODO Remove this
                    },
                },
                "2.0.0": {
                    "messages": {
                        "main_process": {
                            "initial_data": {
                                "status_name": DEFAULT_SCHEDULE_ACTIONS[0],
                                "authorization": {"value": "No"},
                                "reason": {"value": "default"},
                                "theme": {"value": "default"},
                                "bepalen_processtap": {"value": "default"},
                            },
                        },
                        "aanschrijving_toevoegen": {},  # TODO Remove this
                    },
                },
            },
        },
        "housing_corporation": {
            "initial_data": {},
            "versions": {
                "0.1.0": {},
            },
        },
        "renounce_decision": {
            "initial_data": {},
            "versions": {
                "0.1.0": {},
                "0.1.1": {},
            },
        },
        "sub_workflow": {
            "initial_data": {},
            "versions": {
                "0.1.0": {
                    "messages": {
                        "start_signal_process": {},
                        "start_correspondence_process": {},
                        "start_callbackrequest_process": {},
                        "start_objectionfile_process": {},
                    },
                },
                "0.2.0": {
                    "messages": {
                        "start_signal_process": {},
                        "start_correspondence_process": {},
                        "start_callbackrequest_process": {},
                        "start_objectionfile_process": {},
                        "start_extra_information": {},
                        "start_nuisance_process": {},
                        "start_casus_overleg_proces": {},
                    },
                },
            },
        },
        "summon": {
            "initial_data": {
                "task_monitor_incoming_permit_application_timer_duration": timedelta(
                    days=32
                ),
                "task_monitor_permit_request_procedure_timer_duration": timedelta(
                    days=56
                ),
                "task_monitor_incoming_point_of_view_timer_duration": timedelta(
                    days=71
                ),
                "next_step": {"value": "summon"},
                "type_concept_aanschrijving": {"value": "default"},
                "aanschrijving_valide": {"value": "default"},
            },
            "versions": {
                "0.1.0": {},
                "0.2.0": {},
                "1.0.0": {},
                "2.0.0": {},
            },
        },
        "visit": {
            "initial_data": {},
            "versions": {
                "0.1.0": {},
                "0.2.0": {},
                "0.3.0": {},
                "0.4.0": {},
            },
        },
    },
}
