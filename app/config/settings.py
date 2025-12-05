import os
import socket
from datetime import timedelta
from os.path import join

from celery.schedules import crontab
from dotenv import load_dotenv

from .azure_settings import Azure

azure = Azure()

load_dotenv()


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY")

ENVIRONMENT = os.getenv("ENVIRONMENT")
DEBUG = ENVIRONMENT == "local"

# Settings to improve security
is_secure_environment = not DEBUG

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"

USE_TZ = True
TIME_ZONE = "Europe/Amsterdam"

ZAKEN_CONTAINER_HOST = os.getenv("ZAKEN_CONTAINER_HOST")

ALLOWED_HOSTS = ["*"]

CORS_ORIGIN_WHITELIST = os.environ.get("CORS_ORIGIN_WHITELIST").split(",")
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
    "rest_framework",
    "rest_framework.authtoken",
    "drf_spectacular",
    "drf_spectacular_sidecar",  # required for Django collectstatic discovery
    "django_extensions",
    "django_filters",
    "django_celery_beat",
    "django_celery_results",
    "privates",
    "axes",
    # Health checks. (Expand when more services become available)
    "health_check",
    "health_check.db",
    "health_check.contrib.migrations",
    "health_check.contrib.celery_ping",
    # Apps
    "apps.users",
    "apps.cases",
    "apps.decisions",
    "apps.quick_decisions",
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
    "apps.feedback",
)

DATABASE_HOST = os.getenv("DATABASE_HOST", "database")
DATABASE_NAME = os.getenv("DATABASE_NAME", "dev")
DATABASE_USER = os.getenv("DATABASE_USER", "dev")
DATABASE_PASSWORD = os.getenv("DATABASE_PASSWORD", "dev")
DATABASE_PORT = os.getenv("DATABASE_PORT", "5432")
DATABASE_OPTIONS = {"sslmode": "allow", "connect_timeout": 5}

if "azure.com" in DATABASE_HOST:
    DATABASE_PASSWORD = azure.auth.db_password
    DATABASE_OPTIONS["sslmode"] = "require"

DATABASES = {
    "default": {
        "ENGINE": "django.contrib.gis.db.backends.postgis",
        "NAME": DATABASE_NAME,
        "USER": DATABASE_USER,
        "PASSWORD": DATABASE_PASSWORD,
        "HOST": DATABASE_HOST,
        "CONN_MAX_AGE": 60 * 5,
        "PORT": DATABASE_PORT,
        "OPTIONS": {"sslmode": "allow", "connect_timeout": 5},
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
    "apps.cases.middleware.SensitiveCaseMiddleware",
)

STATIC_URL = "/static/"
STATIC_ROOT = os.path.normpath(join(os.path.dirname(BASE_DIR), "static"))

MEDIA_URL = "/media/"
MEDIA_ROOT = os.path.normpath(join(os.path.dirname(BASE_DIR), "media"))

# Make sure that the folder is inside of the .gitignore file
PRIVATE_MEDIA_ROOT = os.path.normpath(join(os.path.dirname(BASE_DIR), "private_media"))

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
    "DEFAULT_PERMISSION_CLASSES": ("apps.users.permissions.IsInAuthorizedRealm",),
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "apps.users.auth.AuthenticationClass",
        "rest_framework.authentication.TokenAuthentication",
    ),
    "EXCEPTION_HANDLER": "utils.exceptions.custom_exception_handler",
}

SPECTACULAR_SETTINGS = {
    "SCHEMA_PATH_PREFIX": "/api/v[0-9]/",
    "TITLE": "Zaken Backend Gateway API",
    "VERSION": "v1",
    "SWAGGER_UI_DIST": "SIDECAR",  # shorthand to use the sidecar instead
    "SWAGGER_UI_FAVICON_HREF": "SIDECAR",
    "REDOC_DIST": "SIDECAR",
}

TAG_NAME = os.getenv("TAG_NAME", "default-release")

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
OIDC_RP_CLIENT_SECRET = os.environ.get("OIDC_RP_CLIENT_SECRET", None)
OIDC_USE_NONCE = False

OIDC_RP_CLIENT_ID = os.environ.get(
    "OIDC_RP_CLIENT_ID", "14c4257b-bcd1-4850-889e-7156c9efe2ec"
)
OIDC_OP_AUTHORIZATION_ENDPOINT = os.getenv(
    "OIDC_OP_AUTHORIZATION_ENDPOINT",
    "https://login.microsoftonline.com/72fca1b1-2c2e-4376-a445-294d80196804/oauth2/v2.0/authorize",
)
OIDC_OP_TOKEN_ENDPOINT = os.getenv(
    "OIDC_OP_TOKEN_ENDPOINT",
    "https://login.microsoftonline.com/72fca1b1-2c2e-4376-a445-294d80196804/oauth2/v2.0/token",
)
OIDC_OP_USER_ENDPOINT = os.getenv(
    "OIDC_OP_USER_ENDPOINT", "https://graph.microsoft.com/oidc/userinfo"
)
OIDC_OP_JWKS_ENDPOINT = os.getenv(
    "OIDC_OP_JWKS_ENDPOINT",
    "https://login.microsoftonline.com/72fca1b1-2c2e-4376-a445-294d80196804/discovery/v2.0/keys",
)
OIDC_RP_SIGN_ALGO = "RS256"
OIDC_OP_ISSUER = os.getenv(
    "OIDC_OP_ISSUER",
    "https://sts.windows.net/72fca1b1-2c2e-4376-a445-294d80196804/",
)

OIDC_TRUSTED_AUDIENCES = f"api://{OIDC_RP_CLIENT_ID}"
OIDC_USE_PKCE = True
OIDC_RP_SCOPES = f"openid email api://{OIDC_RP_CLIENT_ID}/user_impersonation"

LOGIN_URL = "/oidc/authenticate/"

LOCAL_DEVELOPMENT_AUTHENTICATION = (
    os.getenv("LOCAL_DEVELOPMENT_AUTHENTICATION", False) == "True"
)

if LOCAL_DEVELOPMENT_AUTHENTICATION:
    OIDC_AUTHENTICATION_CALLBACK_URL = "oidc-authenticate"

DATA_UPLOAD_MAX_MEMORY_SIZE = 5242880
DATA_UPLOAD_MAX_NUMBER_FIELDS = 6000

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

# Simple JWT is used for local development authentication only.
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(hours=120),
    # We don't refresh tokens yet, so we set refresh lifetime to zero
    "REFRESH_TOKEN_LIFETIME": timedelta(seconds=0),
}

# BAG Atlas
BAG_API_PDOK_URL = os.getenv(
    "BAG_API_PDOK_URL", "https://api.pdok.nl/bzk/locatieserver/search/v3_1/free"
)

# BAG benkagg for nummeraanduidingen and stadsdeel
BAG_API_BENKAGG_SEARCH_URL = os.getenv(
    "BAG_API_BENKAGG_SEARCH_URL",
    "https://api.data.amsterdam.nl/v1/benkagg/adresseerbareobjecten/",
)
# Bag_id of Amstel 1 for testing purposes.
BAG_ID_AMSTEL_1 = os.getenv(
    "BAG_ID_AMSTEL_1",
    "0363010012143319",
)
# Nummeraanduiding_id of Amstel 1 for testing purposes.
NUMMERAANDUIGING_ID_AMSTEL_1 = os.getenv(
    "NUMMERAANDUIGING_ID_AMSTEL_1", "0363200012145295"
)
BELASTING_API_URL = os.getenv(
    "BELASTING_API_URL",
    "https://api-acc.belastingen.centric.eu/bel/inn/afne/vora/v1/vorderingenidentificatienummer/",
)
BELASTING_API_ACCESS_TOKEN = os.getenv("BELASTING_API_ACCESS_TOKEN", None)

BRP_API_URL = "/".join(
    [
        os.getenv(
            "BRP_API_URL", "https://brpproxy.benk-a.azure.amsterdam.nl/entra/brp"
        ),
        "ingeschrevenpersonen",
    ]
)

BRP_CLIENT_ID = os.getenv("BRP_CLIENT_ID", "BRP_CLIENT_ID")
BRP_CLIENT_SECRET = os.getenv("BRP_CLIENT_SECRET", "BRP_CLIENT_SECRET")

# BRP API settings for NEW BRP-API team Benk
BENK_BRP_CLIENT_ID = os.getenv("BENK_BRP_CLIENT_ID", "BENK_BRP_CLIENT_ID")
BENK_BRP_CLIENT_SECRET = os.getenv("BENK_BRP_CLIENT_SECRET", "BENK_BRP_CLIENT_SECRET")
BENK_BRP_SCOPE = os.getenv("BENK_BRP_SCOPE", "BENK_BRP_SCOPE")
BENK_BRP_API_URL = os.getenv(
    "BENK_BRP_API_URL", "https://acc.api.brp.amsterdam.nl/bevragingen/v1/"
)

# Secret keys which can be used to access certain parts of the API
SECRET_KEY_TOP_ZAKEN = os.getenv("SECRET_KEY_TOP_ZAKEN", None)
SECRET_KEY_TON_ZAKEN = os.getenv("SECRET_KEY_TON_ZAKEN", None)

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

# Decos Join Book keys
DECOS_JOIN_B_EN_B_VERGUNNING_ID = "D8D961993D7E478D9B644587822817B1"
DECOS_JOIN_VAKANTIEVERHUURVERGUNNING_ID = "1C0D0EBF55EE49EE872AE1D61433DC21"
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
    "company": "APPLICANT",
    "text19": "HOLDER",
    "subject1": "SUBJECT",
    "text6": "ADDRESS",
    "document_date": "REQUEST_DATE",
}
DECOS_JOIN_BOOK_UNKNOWN_BOOK = "B1FF791EA9FA44698D5ABBB1963B94EC"
DECOS_JOIN_BOOK_KNOWN_BAG_OBJECTS = "90642DCCC2DB46469657C3D0DF0B1ED7"
USE_DECOS_MOCK_DATA = os.getenv("USE_DECOS_MOCK_DATA", False) == "True"

# Powerbrowser for permits
POWERBROWSER_BASE_URL = os.getenv(
    "POWERBROWSER_BASE_URL", "https://accgemeenteamsterdamvth.moverheid.nl/api/"
)
POWERBROWSER_API_KEY = os.getenv("POWERBROWSER_API_KEY")

# TOP Connection settings
SECRET_KEY_AZA_TOP = os.getenv("SECRET_KEY_AZA_TOP")
TOP_API_URL = os.getenv("TOP_API_URL")


def get_redis_url():
    REDIS_HOST = os.getenv("REDIS_HOST")
    REDIS_PORT = os.getenv("REDIS_PORT")
    REDIS_PASSWORD = os.getenv("REDIS_PASSWORD")
    REDIS_PREFIX = "rediss" if is_secure_environment else "redis"
    return f"{REDIS_PREFIX}://:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}"


CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": get_redis_url(),
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
            "SOCKET_CONNECT_TIMEOUT": 5,
            "SOCKET_TIMEOUT": 5,
        },
    }
}

CELERY_TASK_TRACK_STARTED = True
CELERY_BROKER_URL = get_redis_url()
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True
BROKER_CONNECTION_MAX_RETRIES = None
BROKER_CONNECTION_TIMEOUT = 120
BROKER_URL = CELERY_BROKER_URL
CELERY_TASK_TRACK_STARTED = True
CELERY_RESULT_BACKEND = "django-db"
CELERY_TASK_TIME_LIMIT = 5400  # 1,5 hours
CELERY_WORKER_PREFETCH_MULTIPLIER = 1
CELERY_TASK_DEFAULT_PRIORITY = 5
CELERY_BEAT_SCHEDULE = {
    "queue_every_five_mins": {
        "task": "apps.health.tasks.query_every_five_mins",
        "schedule": crontab(minute=5),
    },
}


CELERY_BROKER_TRANSPORT_OPTIONS = {
    "socket_keepalive": True,
    "socket_keepalive_options": {
        socket.TCP_KEEPIDLE: 60,
        socket.TCP_KEEPCNT: 5,
        socket.TCP_KEEPINTVL: 10,
    },
}


LOGOUT_REDIRECT_URL = "/admin"

DEFAULT_THEME = os.getenv("DEFAULT_THEME", "Vakantieverhuur")
DEFAULT_REASON = os.getenv("DEFAULT_REASON", "SIG melding")

DEFAULT_SCHEDULE_ACTIONS = os.getenv("DEFAULT_SCHEDULE_ACTIONS").split(",")
DEFAULT_SCHEDULE_WEEK_SEGMENTS = os.getenv("DEFAULT_SCHEDULE_WEEK_SEGMENTS").split(",")
DEFAULT_SCHEDULE_DAY_SEGMENTS = os.getenv("DEFAULT_SCHEDULE_DAY_SEGMENTS").split(",")
DEFAULT_SCHEDULE_HIGH_PRIORITY = os.getenv("DEFAULT_SCHEDULE_HIGH_PRIORITY")
DEFAULT_SCHEDULE_NORMAL_PRIORITY = os.getenv("DEFAULT_SCHEDULE_NORMAL_PRIORITY")
DIGITAL_SURVEILLANCE_IDS = [12]

VAKANTIEVERHUUR_TOERISTISCHE_VERHUUR_API_URL = os.getenv(
    "VAKANTIEVERHUUR_TOERISTISCHE_VERHUUR_API_URL",
    "https://api.acceptatie.toeristischeverhuur.nl/api/",
)
VAKANTIEVERHUUR_TOERISTISCHE_VERHUUR_API_ACCESS_TOKEN = os.getenv(
    "VAKANTIEVERHUUR_TOERISTISCHE_VERHUUR_API_ACCESS_TOKEN"
)
VAKANTIEVERHUUR_TOERISTISCHE_VERHUUR_API_BSN = os.getenv(
    "VAKANTIEVERHUUR_TOERISTISCHE_VERHUUR_API_BSN"
)

DEFAULT_AUTO_FIELD = "django.db.models.AutoField"

DEFAULT_RSIN = os.getenv("DEFAULT_RSIN", "130365312")

HOST = os.getenv("HOST")

DEFAULT_WORKFLOW_TYPE = os.getenv("DEFAULT_WORKFLOW_TYPE", "director")

CITIZEN_REPORT_FEEDBACK_DEFAULT_FIRST_PERIOD = (
    "54 days, 0:00:00"
    if ENVIRONMENT == "production"
    else os.getenv("CITIZEN_REPORT_FEEDBACK_DEFAULT_FIRST_PERIOD", "0:10:00")
)
CITIZEN_REPORT_FEEDBACK_DEFAULT_SECOND_PERIOD = (
    "26 days, 0:00:00"
    if ENVIRONMENT == "production"
    else os.getenv("CITIZEN_REPORT_FEEDBACK_DEFAULT_SECOND_PERIOD", "0:05:00")
)
CITIZEN_REPORT_FEEDBACK_PERIODS = (
    {
        "themes": (2,),
        "periods": (
            CITIZEN_REPORT_FEEDBACK_DEFAULT_FIRST_PERIOD,
            CITIZEN_REPORT_FEEDBACK_DEFAULT_SECOND_PERIOD,
        ),
    },
)

DEFAULT_WORKFLOW_TIMER_DURATIONS = {
    "local": timedelta(seconds=20),
    "development": timedelta(seconds=20),
    "test": timedelta(seconds=20),
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
            "initial_data": {
                "decision_count": {"value": 0},
                "reason": {"value": "default"},
                "theme": {"value": "default"},
            },
            "versions": {
                "0.1.0": {},
                "0.2.0": {},
                "6.0.0": {},
                "7.0.0": {},
            },
        },
        "decision": {
            "initial_data": {
                "theme": {"value": "default"},
                "task_wait_response_publicate_names_timer_duration": timedelta(days=13),
                "direct_to_check_concept_decision": {"value": "default"},
            },
            "versions": {
                "0.1.0": {},
                "0.2.0": {},
                "7.0.0": {},
                "7.1.0": {},
            },
        },
        "digital_surveillance": {
            "initial_data": {
                "debrief_next_step": {"value": "default"},
                "monitoren_reactie_platform_duration": timedelta(days=14),
            },
            "versions": {
                "3.0.0": {},
                "8.0.0": {},
                "8.1.0": {},
            },
        },
        "debrief": {
            "initial_data": {
                "reason": {"value": "default"},
                "task_afwachten_overgaan_tot_handhaven_timer_duration": timedelta(
                    days=42
                ),
                "task_wait_for_advise_other_discipline_timer_duration": timedelta(
                    days=14
                ),
                "task_wait_for_documents_timer_duration": timedelta(days=14),
                "theme": {"value": "default"},
            },
            "versions": {
                "0.1.0": {},
                "1.0.0": {},
                "2.0.0": {},
                "3.0.0": {},
                "4.0.0": {},
                "4.1.0": {},
                "5.0.0": {},
                "5.1.0": {},
                "7.0.0": {},
                "7.1.0": {},
                "7.2.0": {},
                "7.3.0": {},
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
                        "aanschrijving_toevoegen": {},
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
                        "aanschrijving_toevoegen": {},
                    },
                },
                "2.0.0": {
                    "messages": {
                        "main_process": {
                            "initial_data": {
                                "status_name": DEFAULT_SCHEDULE_ACTIONS[0],
                                "authorization": {"value": "No"},
                                "bepalen_processtap": {"value": "ja"},
                                "reason": {"value": "default"},
                                "theme": {"value": "default"},
                            },
                        },
                        "aanschrijving_toevoegen": {
                            "initial_data": {
                                "status_name": DEFAULT_SCHEDULE_ACTIONS[0],
                                "authorization": {"value": "No"},
                                "bepalen_processtap": {"value": "ja"},
                                "reason": {"value": "default"},
                                "theme": {"value": "default"},
                            },
                        },
                    },
                },
                "3.0.0": {
                    "messages": {
                        "main_process": {
                            "initial_data": {
                                "status_name": DEFAULT_SCHEDULE_ACTIONS[0],
                                "authorization": {"value": "No"},
                                "reason": {"value": "default"},
                                "theme": {"value": "default"},
                                "bepalen_processtap": {"value": "ja"},
                                "debrief_next_step": {"value": "default"},
                                "visit_next_step": {"value": "default"},
                                "monitoren_reactie_platform_duration": timedelta(
                                    days=14
                                ),
                            },
                        },
                        "aanschrijving_toevoegen": {
                            "initial_data": {
                                "status_name": DEFAULT_SCHEDULE_ACTIONS[0],
                                "authorization": {"value": "No"},
                                "reason": {"value": "default"},
                                "theme": {"value": "default"},
                                "bepalen_processtap": {"value": "ja"},
                                "debrief_next_step": {"value": "default"},
                                "visit_next_step": {"value": "default"},
                                "monitoren_reactie_platform_duration": timedelta(
                                    days=14
                                ),
                            },
                        },
                    },
                },
                "4.0.0": {
                    "messages": {
                        "main_process": {
                            "initial_data": {
                                "status_name": DEFAULT_SCHEDULE_ACTIONS[0],
                                "authorization": {"value": "No"},
                                "reason": {"value": "default"},
                                "theme": {"value": "default"},
                                "bepalen_processtap": {"value": "ja"},
                                "debrief_next_step": {"value": "default"},
                                "summon_next_step": {"value": "default"},
                                "visit_next_step": {"value": "default"},
                                "monitoren_reactie_platform_duration": timedelta(
                                    days=14
                                ),
                                "leegstandsmelding_eigenaar": {"value": "default"},
                            },
                        },
                        "aanschrijving_toevoegen": {
                            "initial_data": {
                                "status_name": DEFAULT_SCHEDULE_ACTIONS[0],
                                "authorization": {"value": "No"},
                                "reason": {"value": "default"},
                                "theme": {"value": "default"},
                                "bepalen_processtap": {"value": "ja"},
                                "debrief_next_step": {"value": "default"},
                                "summon_next_step": {"value": "default"},
                                "visit_next_step": {"value": "default"},
                                "monitoren_reactie_platform_duration": timedelta(
                                    days=14
                                ),
                                "leegstandsmelding_eigenaar": {"value": "default"},
                            },
                        },
                    },
                },
                "5.0.0": {
                    "messages": {
                        "main_process": {
                            "initial_data": {
                                "status_name": DEFAULT_SCHEDULE_ACTIONS[0],
                                "authorization": {"value": "No"},
                                "reason": {"value": "default"},
                                "theme": {"value": "default"},
                                "bepalen_processtap": {"value": "ja"},
                                "debrief_next_step": {"value": "default"},
                                "summon_next_step": {"value": "default"},
                                "visit_next_step": {"value": "default"},
                                "housing_corporation_next_step": {"value": "default"},
                                "monitoren_reactie_platform_duration": timedelta(
                                    days=14
                                ),
                                "leegstandsmelding_eigenaar": {"value": "default"},
                            },
                        },
                        "aanschrijving_toevoegen": {
                            "initial_data": {
                                "status_name": DEFAULT_SCHEDULE_ACTIONS[0],
                                "authorization": {"value": "No"},
                                "reason": {"value": "default"},
                                "theme": {"value": "default"},
                                "bepalen_processtap": {"value": "ja"},
                                "debrief_next_step": {"value": "default"},
                                "summon_next_step": {"value": "default"},
                                "visit_next_step": {"value": "default"},
                                "housing_corporation_next_step": {"value": "default"},
                                "monitoren_reactie_platform_duration": timedelta(
                                    days=14
                                ),
                                "leegstandsmelding_eigenaar": {"value": "default"},
                            },
                        },
                    },
                },
                "5.1.0": {
                    "messages": {
                        "main_process": {
                            "initial_data": {
                                "status_name": DEFAULT_SCHEDULE_ACTIONS[0],
                                "authorization": {"value": "No"},
                                "reason": {"value": "default"},
                                "theme": {"value": "default"},
                                "bepalen_processtap": {"value": "ja"},
                                "debrief_next_step": {"value": "default"},
                                "summon_next_step": {"value": "default"},
                                "visit_next_step": {"value": "default"},
                                "housing_corporation_next_step": {"value": "default"},
                                "monitoren_reactie_platform_duration": timedelta(
                                    days=14
                                ),
                                "leegstandsmelding_eigenaar": {"value": "default"},
                            },
                        },
                        "aanschrijving_toevoegen": {
                            "initial_data": {
                                "status_name": DEFAULT_SCHEDULE_ACTIONS[0],
                                "authorization": {"value": "No"},
                                "reason": {"value": "default"},
                                "theme": {"value": "default"},
                                "bepalen_processtap": {"value": "ja"},
                                "debrief_next_step": {"value": "default"},
                                "summon_next_step": {"value": "default"},
                                "visit_next_step": {"value": "default"},
                                "housing_corporation_next_step": {"value": "default"},
                                "monitoren_reactie_platform_duration": timedelta(
                                    days=14
                                ),
                                "leegstandsmelding_eigenaar": {"value": "default"},
                            },
                        },
                    },
                },
                "6.0.0": {
                    "messages": {
                        "main_process": {
                            "initial_data": {
                                "status_name": DEFAULT_SCHEDULE_ACTIONS[0],
                                "authorization": {"value": "No"},
                                "reason": {"value": "default"},
                                "theme": {"value": "default"},
                                "bepalen_processtap": {"value": "ja"},
                                "debrief_next_step": {"value": "default"},
                                "summon_next_step": {"value": "default"},
                                "visit_next_step": {"value": "default"},
                                "housing_corporation_next_step": {"value": "default"},
                                "monitoren_reactie_platform_duration": timedelta(
                                    days=14
                                ),
                                "leegstandsmelding_eigenaar": {"value": "default"},
                            },
                        },
                        "aanschrijving_toevoegen": {
                            "initial_data": {
                                "status_name": DEFAULT_SCHEDULE_ACTIONS[0],
                                "authorization": {"value": "No"},
                                "reason": {"value": "default"},
                                "theme": {"value": "default"},
                                "bepalen_processtap": {"value": "ja"},
                                "debrief_next_step": {"value": "default"},
                                "summon_next_step": {"value": "default"},
                                "visit_next_step": {"value": "default"},
                                "housing_corporation_next_step": {"value": "default"},
                                "monitoren_reactie_platform_duration": timedelta(
                                    days=14
                                ),
                                "leegstandsmelding_eigenaar": {"value": "default"},
                            },
                        },
                    },
                },
                "7.0.0": {
                    "messages": {
                        "main_process": {
                            "initial_data": {
                                "status_name": DEFAULT_SCHEDULE_ACTIONS[0],
                                "authorization": {"value": "No"},
                                "reason": {"value": "default"},
                                "theme": {"value": "default"},
                                "bepalen_processtap": {"value": "ja"},
                                "debrief_next_step": {"value": "default"},
                                "summon_next_step": {"value": "default"},
                                "visit_next_step": {"value": "default"},
                                "housing_corporation_next_step": {"value": "default"},
                                "monitoren_reactie_platform_duration": timedelta(
                                    days=14
                                ),
                                "leegstandsmelding_eigenaar": {"value": "default"},
                            },
                        },
                        "aanschrijving_toevoegen": {
                            "initial_data": {
                                "status_name": DEFAULT_SCHEDULE_ACTIONS[0],
                                "authorization": {"value": "No"},
                                "reason": {"value": "default"},
                                "theme": {"value": "default"},
                                "bepalen_processtap": {"value": "ja"},
                                "debrief_next_step": {"value": "default"},
                                "summon_next_step": {"value": "default"},
                                "visit_next_step": {"value": "default"},
                                "housing_corporation_next_step": {"value": "default"},
                                "monitoren_reactie_platform_duration": timedelta(
                                    days=14
                                ),
                                "leegstandsmelding_eigenaar": {"value": "default"},
                            },
                        },
                    },
                },
                "7.1.0": {
                    "messages": {
                        "main_process": {
                            "initial_data": {
                                "status_name": DEFAULT_SCHEDULE_ACTIONS[0],
                                "authorization": {"value": "No"},
                                "reason": {"value": "default"},
                                "theme": {"value": "default"},
                                "bepalen_processtap": {"value": "ja"},
                                "debrief_next_step": {"value": "default"},
                                "summon_next_step": {"value": "default"},
                                "visit_next_step": {"value": "default"},
                                "housing_corporation_next_step": {"value": "default"},
                                "monitoren_reactie_platform_duration": timedelta(
                                    days=14
                                ),
                                "leegstandsmelding_eigenaar": {"value": "default"},
                            },
                        },
                        "aanschrijving_toevoegen": {
                            "initial_data": {
                                "status_name": DEFAULT_SCHEDULE_ACTIONS[0],
                                "authorization": {"value": "No"},
                                "reason": {"value": "default"},
                                "theme": {"value": "default"},
                                "bepalen_processtap": {"value": "ja"},
                                "debrief_next_step": {"value": "default"},
                                "summon_next_step": {"value": "default"},
                                "visit_next_step": {"value": "default"},
                                "housing_corporation_next_step": {"value": "default"},
                                "monitoren_reactie_platform_duration": timedelta(
                                    days=14
                                ),
                                "leegstandsmelding_eigenaar": {"value": "default"},
                            },
                        },
                    },
                },
                "8.0.0": {
                    "messages": {
                        "main_process": {
                            "initial_data": {
                                "status_name": DEFAULT_SCHEDULE_ACTIONS[0],
                                "authorization": {"value": "No"},
                                "reason": {"value": "default"},
                                "theme": {"value": "default"},
                                "bepalen_processtap": {"value": "ja"},
                                "debrief_next_step": {"value": "default"},
                                "summon_next_step": {"value": "default"},
                                "visit_next_step": {"value": "default"},
                                "housing_corporation_next_step": {"value": "default"},
                                "monitoren_reactie_platform_duration": timedelta(
                                    days=14
                                ),
                                "leegstandsmelding_eigenaar": {"value": "default"},
                            },
                        },
                        "aanschrijving_toevoegen": {
                            "initial_data": {
                                "status_name": DEFAULT_SCHEDULE_ACTIONS[0],
                                "authorization": {"value": "No"},
                                "reason": {"value": "default"},
                                "theme": {"value": "default"},
                                "bepalen_processtap": {"value": "ja"},
                                "debrief_next_step": {"value": "default"},
                                "summon_next_step": {"value": "default"},
                                "visit_next_step": {"value": "default"},
                                "housing_corporation_next_step": {"value": "default"},
                                "monitoren_reactie_platform_duration": timedelta(
                                    days=14
                                ),
                                "leegstandsmelding_eigenaar": {"value": "default"},
                            },
                        },
                    },
                },
                "8.1.0": {
                    "messages": {
                        "main_process": {
                            "initial_data": {
                                "status_name": DEFAULT_SCHEDULE_ACTIONS[0],
                                "authorization": {"value": "No"},
                                "reason": {"value": "default"},
                                "theme": {"value": "default"},
                                "bepalen_processtap": {"value": "ja"},
                                "debrief_next_step": {"value": "default"},
                                "summon_next_step": {"value": "default"},
                                "visit_next_step": {"value": "default"},
                                "housing_corporation_next_step": {"value": "default"},
                                "monitoren_reactie_platform_duration": timedelta(
                                    days=14
                                ),
                                "leegstandsmelding_eigenaar": {"value": "default"},
                            },
                        },
                        "aanschrijving_toevoegen": {
                            "initial_data": {
                                "status_name": DEFAULT_SCHEDULE_ACTIONS[0],
                                "authorization": {"value": "No"},
                                "reason": {"value": "default"},
                                "theme": {"value": "default"},
                                "bepalen_processtap": {"value": "ja"},
                                "debrief_next_step": {"value": "default"},
                                "summon_next_step": {"value": "default"},
                                "visit_next_step": {"value": "default"},
                                "housing_corporation_next_step": {"value": "default"},
                                "monitoren_reactie_platform_duration": timedelta(
                                    days=14
                                ),
                                "leegstandsmelding_eigenaar": {"value": "default"},
                            },
                        },
                    },
                },
            },
        },
        "housing_corporation": {
            "initial_data": {
                "task_monitoren_reactie_corporatie_voor_huisbezoek_timer_duration": timedelta(
                    days=14
                ),
                "task_afwachten_besluit_corporatie_na_huisbezoek_1_timer_duration": timedelta(
                    days=56
                ),
                "task_afwachten_besluit_corporatie_na_huisbezoek_2_timer_duration": timedelta(
                    days=84
                ),
            },
            "versions": {
                "5.0.0": {},
                "6.1.0": {},
                "6.2.0": {},
            },
        },
        "renounce_decision": {
            "initial_data": {},
            "versions": {
                "0.1.0": {},
                "0.1.1": {},
                "0.1.2": {},
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
                "0.3.0": {
                    "messages": {
                        "start_signal_process": {},
                        "start_correspondence_process": {},
                        "start_callbackrequest_process": {},
                        "start_objectionfile_process": {},
                        "start_extra_information": {},
                        "start_nuisance_process": {},
                        "start_casus_overleg_proces": {},
                        "start_opstellen_digitale_analyse_proces": {},
                        "start_aanleveren_wob_dossier": {},
                        "start_terugkoppelen_bi": {},
                    },
                },
                "0.4.0": {
                    "messages": {
                        "start_signal_process": {},
                        "start_correspondence_process": {},
                        "start_callbackrequest_process": {},
                        "start_objectionfile_process": {},
                        "start_extra_information": {},
                        "start_nuisance_process": {},
                        "start_casus_overleg_proces": {},
                        "start_opstellen_digitale_analyse_proces": {},
                        "start_aanleveren_wob_dossier": {},
                        "start_terugkoppelen_bi": {},
                    },
                },
                "0.5.0": {
                    "messages": {
                        "start_signal_process": {},
                        "start_correspondence_process": {},
                        "start_callbackrequest_process": {},
                        "start_objectionfile_process": {},
                        "start_extra_information": {},
                        "start_nuisance_process": {},
                        "start_casus_overleg_proces": {},
                        "start_opstellen_digitale_analyse_proces": {},
                        "start_aanleveren_wob_dossier": {},
                        "start_terugkoppelen_bi": {},
                        "start_uitkomst_corporatie_proces": {},
                    },
                },
                "0.6.0": {
                    "messages": {
                        "start_signal_process": {},
                        "start_correspondence_process": {},
                        "start_callbackrequest_process": {},
                        "start_objectionfile_process": {},
                        "start_extra_information": {},
                        "start_nuisance_process": {},
                        "start_casus_overleg_proces": {},
                        "start_opstellen_digitale_analyse_proces": {},
                        "start_aanleveren_wob_dossier": {},
                        "start_terugkoppelen_bi": {},
                        "start_uitkomst_corporatie_proces": {},
                        "start_rapport_bewoners": {},
                    },
                },
                "0.7.0": {
                    "messages": {
                        "start_signal_process": {},
                        "start_correspondence_process": {},
                        "start_callbackrequest_process": {},
                        "start_objectionfile_process": {},
                        "start_extra_information": {},
                        "start_nuisance_process": {},
                        "start_casus_overleg_proces": {},
                        "start_opstellen_digitale_analyse_proces": {},
                        "start_aanleveren_wob_dossier": {},
                        "start_terugkoppelen_bi": {},
                        "start_uitkomst_corporatie_proces": {},
                        "start_rapport_bewoners": {},
                        "start_afsluiten_zaak": {},
                        "start_handhavingsverzoek": {},
                        "start_ingebrekestelling": {},
                        "start_uit_termijn_lopen": {},
                    },
                },
                "0.8.0": {
                    "messages": {
                        "start_signal_process": {},
                        "start_correspondence_process": {},
                        "start_callbackrequest_process": {},
                        "start_objectionfile_process": {},
                        "start_extra_information": {},
                        "start_nuisance_process": {},
                        "start_casus_overleg_proces": {},
                        "start_opstellen_digitale_analyse_proces": {},
                        "start_aanleveren_wob_dossier": {},
                        "start_terugkoppelen_bi": {},
                        "start_uitkomst_corporatie_proces": {},
                        "start_rapport_bewoners": {},
                        "start_afsluiten_zaak": {},
                        "start_mma_signal_process": {},
                        "start_doorzon_signal_process": {},
                    },
                },
                "0.9.0": {
                    "messages": {
                        "start_signal_process": {},
                        "start_correspondence_process": {},
                        "start_callbackrequest_process": {},
                        "start_objectionfile_process": {},
                        "start_extra_information": {},
                        "start_nuisance_process": {},
                        "start_casus_overleg_proces": {},
                        "start_opstellen_digitale_analyse_proces": {},
                        "start_aanleveren_wob_dossier": {},
                        "start_terugkoppelen_bi": {},
                        "start_uitkomst_corporatie_proces": {},
                        "start_rapport_bewoners": {},
                        "start_afsluiten_zaak": {},
                        "start_mma_signal_process": {},
                        "start_lod_verzoek_tot_opheffing": {},
                    },
                },
                "7.0.0": {
                    "messages": {
                        "start_signal_process": {},
                        "start_correspondence_process": {},
                        "start_callbackrequest_process": {},
                        "start_objectionfile_process": {},
                        "start_extra_information": {},
                        "start_nuisance_process": {},
                        "start_casus_overleg_proces": {},
                        "start_opstellen_digitale_analyse_proces": {},
                        "start_aanleveren_wob_dossier": {},
                        "start_terugkoppelen_bi": {},
                        "start_uitkomst_corporatie_proces": {},
                        "start_rapport_bewoners": {},
                        "start_afsluiten_zaak": {},
                        "start_mma_signal_process": {},
                        "start_lod_verzoek_tot_opheffing": {},
                        "start_verzoek_opheffing_openbaarmaking_namen": {},
                    },
                },
                "7.1.0": {
                    "messages": {
                        "start_signal_process": {},
                        "start_correspondence_process": {},
                        "start_callbackrequest_process": {},
                        "start_objectionfile_process": {},
                        "start_extra_information": {},
                        "start_nuisance_process": {},
                        "start_casus_overleg_proces": {},
                        "start_opstellen_digitale_analyse_proces": {},
                        "start_aanleveren_wob_dossier": {},
                        "start_terugkoppelen_bi": {},
                        "start_uitkomst_corporatie_proces": {},
                        "start_rapport_bewoners": {},
                        "start_afsluiten_zaak": {},
                        "start_mma_signal_process": {},
                        "start_lod_verzoek_tot_opheffing": {},
                        "start_verzoek_opheffing_openbaarmaking_namen": {},
                        "start_doorzon_pv": {},
                        "start_terugmelding_bag": {},
                    },
                },
                "7.2.0": {
                    "messages": {
                        "start_signal_process": {},
                        "start_correspondence_process": {},
                        "start_callbackrequest_process": {},
                        "start_objectionfile_process": {},
                        "start_extra_information": {},
                        "start_nuisance_process": {},
                        "start_casus_overleg_proces": {},
                        "start_opstellen_digitale_analyse_proces": {},
                        "start_aanleveren_wob_dossier": {},
                        "start_terugkoppelen_bi": {},
                        "start_uitkomst_corporatie_proces": {},
                        "start_rapport_bewoners": {},
                        "start_afsluiten_zaak": {},
                        "start_mma_signal_process": {},
                        "start_lod_verzoek_tot_opheffing": {},
                        "start_verzoek_opheffing_openbaarmaking_namen": {},
                        "start_doorzon_pv": {},
                        "start_terugmelding_bag": {},
                        "start_doorzetten_stukken_woningcorporatie": {},
                        "start_doorzetten_bestuurlijk_prostitutie": {},
                        "start_doorzetten_stukken_stadsdeel": {},
                        "start_bewustwordingsgesprek_eigenaar": {},
                        "start_informatieverzoek": {},
                    },
                },
                "7.3.0": {
                    "messages": {
                        "start_aanleveren_wob_dossier": {},
                        "start_aanvullend_huisbezoek": {},
                        "start_afsluiten_zaak": {},
                        "start_bewustwordingsgesprek_eigenaar": {},
                        "start_callbackrequest_process": {},
                        "start_casus_overleg_proces": {},
                        "start_correspondence_process": {},
                        "start_doorzetten_bestuurlijk_prostitutie": {},
                        "start_doorzetten_stukken_stadsdeel": {},
                        "start_doorzetten_stukken_woningcorporatie": {},
                        "start_doorzon_pv": {},
                        "start_doorzon_signal_process": {},
                        "start_extra_information": {},
                        "start_handhavingsverzoek": {},
                        "start_ingebrekestelling": {},
                        "start_informatieverzoek": {},
                        "start_lod_verzoek_tot_opheffing": {},
                        "start_mma_signal_process": {},
                        "start_nuisance_process": {},
                        "start_objectionfile_process": {},
                        "start_opstellen_digitale_analyse_proces": {},
                        "start_rapport_bewoners": {},
                        "start_signal_process": {},
                        "start_terugkoppelen_bi": {},
                        "start_terugmelding_bag": {},
                        "start_uit_termijn_lopen": {},
                        "start_uitkomst_corporatie_proces": {},
                        "start_verzoek_opheffing_openbaarmaking_namen": {},
                    },
                },
                "7.4.0": {
                    "messages": {
                        "start_aanleveren_wob_dossier": {},
                        "start_aanvullend_huisbezoek": {},
                        "start_afsluiten_zaak": {},
                        "start_bewustwordingsgesprek_eigenaar": {},
                        "start_callbackrequest_process": {},
                        "start_casus_overleg_proces": {},
                        "start_correspondence_process": {},
                        "start_doorzetten_bestuurlijk_prostitutie": {},
                        "start_doorzetten_stukken_stadsdeel": {},
                        "start_doorzetten_stukken_woningcorporatie": {},
                        "start_doorzon_pv": {},
                        "start_doorzon_signal_process": {},
                        "start_extra_information": {},
                        "start_handhavingsverzoek": {},
                        "start_ingebrekestelling": {},
                        "start_informatieverzoek": {},
                        "start_lod_verzoek_tot_opheffing": {},
                        "start_mma_signal_process": {},
                        "start_nuisance_process": {},
                        "start_objectionfile_process": {},
                        "start_opstellen_digitale_analyse_proces": {},
                        "start_rapport_bewoners": {},
                        "start_signal_process": {},
                        "start_terugkoppelen_bi": {},
                        "start_terugmelding_bag": {},
                        "start_uit_termijn_lopen": {},
                        "start_uitkomst_corporatie_proces": {},
                        "start_verzoek_opheffing_openbaarmaking_namen": {},
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
                    days=17
                ),
                "monitoren_reactie_platform_duration": timedelta(days=14),
                "next_step": {"value": "summon"},
                "type_concept_aanschrijving": {"value": "default"},
                "aanschrijving_valide": {"value": "default"},
                "direct_to_check_summons": {"value": "No"},
            },
            "versions": {
                "0.1.0": {},
                "0.2.0": {},
                "1.0.0": {},
                "2.0.0": {},
                "3.0.0": {},
                "4.0.0": {},
                "4.1.0": {},
                "6.3.0": {},
                "7.1.0": {},
                "7.2.0": {},
                "7.3.0": {},
                "7.4.0": {},
            },
        },
        "unoccupied": {
            "initial_data": {
                "task_leegstand_monitoren_binnenkomen_reactie_timer_duration": timedelta(
                    days=18
                ),
                "task_leegstand_monitoren_binnenkomen_melding_timer_duration": timedelta(
                    days=18
                ),
                "task_afwachten_afspraken_periode_timer_duration": timedelta(days=7),
                "constateringsbrief_proces": "ja",
            },
            "versions": {
                "4.0.0": {},
                "4.0.1": {},
                "7.1.0": {},
            },
        },
        "visit": {
            "initial_data": {
                "bepalen_processtap": {"value": "default"},
                "status_name": DEFAULT_SCHEDULE_ACTIONS[0],
            },
            "versions": {
                "0.1.0": {},
                "0.2.0": {},
                "0.3.0": {},
                "0.4.0": {},
                "0.5.0": {},
                "0.6.0": {},
                "8.0.0": {},
            },
        },
        "citizen_report_feedback": {
            "initial_data": {
                "force_citizen_report_feedback": {"value": False},
            },
            "versions": {
                "0.1.0": {},
            },
        },
    },
}

SLACK_WEBHOOK_URL = os.getenv(
    "SLACK_WEBHOOK_URL", "https://hooks.slack.com/services/test/test/test"
)

MIMETYPES_FALLBACK = {
    "x3d": "application/vnd.hzn-3d-crossword",
    "3gp": "video/3gpp",
    "3g2": "video/3gpp2",
    "mseq": "application/vnd.mseq",
    "pwn": "application/vnd.3m.post-it-notes",
    "plb": "application/vnd.3gpp.pic-bw-large",
    "psb": "application/vnd.3gpp.pic-bw-small",
    "pvb": "application/vnd.3gpp.pic-bw-var",
    "tcap": "application/vnd.3gpp2.tcap",
    "7z": "application/x-7z-compressed",
    "abw": "application/x-abiword",
    "ace": "application/x-ace-compressed",
    "acc": "application/vnd.americandynamics.acc",
    "acu": "application/vnd.acucobol",
    "atc": "application/vnd.acucorp",
    "adp": "audio/adpcm",
    "aab": "application/x-authorware-bin",
    "aam": "application/x-authorware-map",
    "aas": "application/x-authorware-seg",
    "air": "application/vnd.adobe.air-application-installer-package+zip",
    "swf": "application/x-shockwave-flash",
    "fxp": "application/vnd.adobe.fxp",
    "pdf": "application/pdf",
    "ppd": "application/vnd.cups-ppd",
    "dir": "application/x-director",
    "xdp": "application/vnd.adobe.xdp+xml",
    "xfdf": "application/vnd.adobe.xfdf",
    "aac": "audio/x-aac",
    "ahead": "application/vnd.ahead.space",
    "azf": "application/vnd.airzip.filesecure.azf",
    "azs": "application/vnd.airzip.filesecure.azs",
    "azw": "application/vnd.amazon.ebook",
    "ami": "application/vnd.amiga.ami",
    "N/A": "application/andrew-inset",
    "apk": "application/vnd.android.package-archive",
    "cii": "application/vnd.anser-web-certificate-issue-initiation",
    "fti": "application/vnd.anser-web-funds-transfer-initiation",
    "atx": "application/vnd.antix.game-component",
    "dmg": "application/x-apple-diskimage",
    "mpkg": "application/vnd.apple.installer+xml",
    "aw": "application/applixware",
    "mp3": "audio/mpeg",
    "les": "application/vnd.hhe.lesson-player",
    "swi": "application/vnd.aristanetworks.swi",
    "s": "text/x-asm",
    "atomcat": "application/atomcat+xml",
    "atomsvc": "application/atomsvc+xml",
    "atom, .xml": "application/atom+xml",
    "ac": "application/pkix-attr-cert",
    "aif": "audio/x-aiff",
    "avi": "video/x-msvideo",
    "aep": "application/vnd.audiograph",
    "dxf": "image/vnd.dxf",
    "dwf": "model/vnd.dwf",
    "par": "text/plain-bas",
    "bcpio": "application/x-bcpio",
    "bin": "application/octet-stream",
    "bmp": "image/bmp",
    "torrent": "application/x-bittorrent",
    "cod": "application/vnd.rim.cod",
    "mpm": "application/vnd.blueice.multipass",
    "bmi": "application/vnd.bmi",
    "sh": "application/x-sh",
    "btif": "image/prs.btif",
    "rep": "application/vnd.businessobjects",
    "bz": "application/x-bzip",
    "bz2": "application/x-bzip2",
    "csh": "application/x-csh",
    "c": "text/x-c",
    "cdxml": "application/vnd.chemdraw+xml",
    "css": "text/css",
    "cdx": "chemical/x-cdx",
    "cml": "chemical/x-cml",
    "csml": "chemical/x-csml",
    "cdbcmsg": "application/vnd.contact.cmsg",
    "cla": "application/vnd.claymore",
    "c4g": "application/vnd.clonk.c4group",
    "sub": "image/vnd.dvb.subtitle",
    "cdmia": "application/cdmi-capability",
    "cdmic": "application/cdmi-container",
    "cdmid": "application/cdmi-domain",
    "cdmio": "application/cdmi-object",
    "cdmiq": "application/cdmi-queue",
    "c11amc": "application/vnd.cluetrust.cartomobile-config",
    "c11amz": "application/vnd.cluetrust.cartomobile-config-pkg",
    "ras": "image/x-cmu-raster",
    "dae": "model/vnd.collada+xml",
    "csv": "text/csv",
    "cpt": "application/mac-compactpro",
    "wmlc": "application/vnd.wap.wmlc",
    "cgm": "image/cgm",
    "ice": "x-conference/x-cooltalk",
    "cmx": "image/x-cmx",
    "xar": "application/vnd.xara",
    "cmc": "application/vnd.cosmocaller",
    "cpio": "application/x-cpio",
    "clkx": "application/vnd.crick.clicker",
    "clkk": "application/vnd.crick.clicker.keyboard",
    "clkp": "application/vnd.crick.clicker.palette",
    "clkt": "application/vnd.crick.clicker.template",
    "clkw": "application/vnd.crick.clicker.wordbank",
    "wbs": "application/vnd.criticaltools.wbs+xml",
    "cryptonote": "application/vnd.rig.cryptonote",
    "cif": "chemical/x-cif",
    "cmdf": "chemical/x-cmdf",
    "cu": "application/cu-seeme",
    "cww": "application/prs.cww",
    "curl": "text/vnd.curl",
    "dcurl": "text/vnd.curl.dcurl",
    "mcurl": "text/vnd.curl.mcurl",
    "scurl": "text/vnd.curl.scurl",
    "car": "application/vnd.curl.car",
    "pcurl": "application/vnd.curl.pcurl",
    "cmp": "application/vnd.yellowriver-custom-menu",
    "dssc": "application/dssc+der",
    "xdssc": "application/dssc+xml",
    "deb": "application/x-debian-package",
    "uva": "audio/vnd.dece.audio",
    "uvi": "image/vnd.dece.graphic",
    "uvh": "video/vnd.dece.hd",
    "uvm": "video/vnd.dece.mobile",
    "uvu": "video/vnd.uvvu.mp4",
    "uvp": "video/vnd.dece.pd",
    "uvs": "video/vnd.dece.sd",
    "uvv": "video/vnd.dece.video",
    "dvi": "application/x-dvi",
    "seed": "application/vnd.fdsn.seed",
    "dtb": "application/x-dtbook+xml",
    "res": "application/x-dtbresource+xml",
    "ait": "application/vnd.dvb.ait",
    "svc": "application/vnd.dvb.service",
    "eol": "audio/vnd.digital-winds",
    "djvu": "image/vnd.djvu",
    "dtd": "application/xml-dtd",
    "mlp": "application/vnd.dolby.mlp",
    "wad": "application/x-doom",
    "dpg": "application/vnd.dpgraph",
    "dra": "audio/vnd.dra",
    "dfac": "application/vnd.dreamfactory",
    "dts": "audio/vnd.dts",
    "dtshd": "audio/vnd.dts.hd",
    "dwg": "image/vnd.dwg",
    "geo": "application/vnd.dynageo",
    "es": "application/ecmascript",
    "mag": "application/vnd.ecowin.chart",
    "mmr": "image/vnd.fujixerox.edmics-mmr",
    "rlc": "image/vnd.fujixerox.edmics-rlc",
    "exi": "application/exi",
    "mgz": "application/vnd.proteus.magazine",
    "epub": "application/epub+zip",
    "eml": "message/rfc822",
    "nml": "application/vnd.enliven",
    "xpr": "application/vnd.is-xpr",
    "xif": "image/vnd.xiff",
    "xfdl": "application/vnd.xfdl",
    "emma": "application/emma+xml",
    "ez2": "application/vnd.ezpix-album",
    "ez3": "application/vnd.ezpix-package",
    "fst": "image/vnd.fst",
    "fvt": "video/vnd.fvt",
    "fbs": "image/vnd.fastbidsheet",
    "fe_launch": "application/vnd.denovo.fcselayout-link",
    "f4v": "video/x-f4v",
    "flv": "video/x-flv",
    "fpx": "image/vnd.fpx",
    "npx": "image/vnd.net-fpx",
    "flx": "text/vnd.fmi.flexstor",
    "fli": "video/x-fli",
    "ftc": "application/vnd.fluxtime.clip",
    "fdf": "application/vnd.fdf",
    "f": "text/x-fortran",
    "mif": "application/vnd.mif",
    "fm": "application/vnd.framemaker",
    "fh": "image/x-freehand",
    "fsc": "application/vnd.fsc.weblaunch",
    "fnc": "application/vnd.frogans.fnc",
    "ltf": "application/vnd.frogans.ltf",
    "ddd": "application/vnd.fujixerox.ddd",
    "xdw": "application/vnd.fujixerox.docuworks",
    "xbd": "application/vnd.fujixerox.docuworks.binder",
    "oas": "application/vnd.fujitsu.oasys",
    "oa2": "application/vnd.fujitsu.oasys2",
    "oa3": "application/vnd.fujitsu.oasys3",
    "fg5": "application/vnd.fujitsu.oasysgp",
    "bh2": "application/vnd.fujitsu.oasysprs",
    "spl": "application/x-futuresplash",
    "fzs": "application/vnd.fuzzysheet",
    "g3": "image/g3fax",
    "gmx": "application/vnd.gmx",
    "gtw": "model/vnd.gtw",
    "txd": "application/vnd.genomatix.tuxedo",
    "ggb": "application/vnd.geogebra.file",
    "ggt": "application/vnd.geogebra.tool",
    "gdl": "model/vnd.gdl",
    "gex": "application/vnd.geometry-explorer",
    "gxt": "application/vnd.geonext",
    "g2w": "application/vnd.geoplan",
    "g3w": "application/vnd.geospace",
    "gsf": "application/x-font-ghostscript",
    "bdf": "application/x-font-bdf",
    "gtar": "application/x-gtar",
    "texinfo": "application/x-texinfo",
    "gnumeric": "application/x-gnumeric",
    "kml": "application/vnd.google-earth.kml+xml",
    "kmz": "application/vnd.google-earth.kmz",
    "gqf": "application/vnd.grafeq",
    "gif": "image/gif",
    "gv": "text/vnd.graphviz",
    "gac": "application/vnd.groove-account",
    "ghf": "application/vnd.groove-help",
    "gim": "application/vnd.groove-identity-message",
    "grv": "application/vnd.groove-injector",
    "gtm": "application/vnd.groove-tool-message",
    "tpl": "application/vnd.groove-tool-template",
    "vcg": "application/vnd.groove-vcard",
    "h261": "video/h261",
    "h263": "video/h263",
    "h264": "video/h264",
    "hpid": "application/vnd.hp-hpid",
    "hps": "application/vnd.hp-hps",
    "hdf": "application/x-hdf",
    "rip": "audio/vnd.rip",
    "hbci": "application/vnd.hbci",
    "jlt": "application/vnd.hp-jlyt",
    "pcl": "application/vnd.hp-pcl",
    "hpgl": "application/vnd.hp-hpgl",
    "hvs": "application/vnd.yamaha.hv-script",
    "hvd": "application/vnd.yamaha.hv-dic",
    "hvp": "application/vnd.yamaha.hv-voice",
    "sfd-hdstx": "application/vnd.hydrostatix.sof-data",
    "stk": "application/hyperstudio",
    "hal": "application/vnd.hal+xml",
    "html": "text/html",
    "irm": "application/vnd.ibm.rights-management",
    "sc": "application/vnd.ibm.secure-container",
    "ics": "text/calendar",
    "icc": "application/vnd.iccprofile",
    "ico": "image/x-icon",
    "igl": "application/vnd.igloader",
    "ief": "image/ief",
    "ivp": "application/vnd.immervision-ivp",
    "ivu": "application/vnd.immervision-ivu",
    "rif": "application/reginfo+xml",
    "3dml": "text/vnd.in3d.3dml",
    "spot": "text/vnd.in3d.spot",
    "igs": "model/iges",
    "i2g": "application/vnd.intergeo",
    "cdy": "application/vnd.cinderella",
    "xpw": "application/vnd.intercon.formnet",
    "fcs": "application/vnd.isac.fcs",
    "ipfix": "application/ipfix",
    "cer": "application/pkix-cert",
    "pki": "application/pkixcmp",
    "crl": "application/pkix-crl",
    "pkipath": "application/pkix-pkipath",
    "igm": "application/vnd.insors.igm",
    "rcprofile": "application/vnd.ipunplugged.rcprofile",
    "irp": "application/vnd.irepository.package+xml",
    "jad": "text/vnd.sun.j2me.app-descriptor",
    "jar": "application/java-archive",
    "class": "application/java-vm",
    "jnlp": "application/x-java-jnlp-file",
    "ser": "application/java-serialized-object",
    "java": "text/x-java-source,java",
    "js": "application/javascript",
    "json": "application/json",
    "joda": "application/vnd.joost.joda-archive",
    "jpm": "video/jpm",
    "jpeg, .jpg": "image/x-citrix-jpeg",
    "pjpeg": "image/pjpeg",
    "jpgv": "video/jpeg",
    "ktz": "application/vnd.kahootz",
    "mmd": "application/vnd.chipnuts.karaoke-mmd",
    "karbon": "application/vnd.kde.karbon",
    "chrt": "application/vnd.kde.kchart",
    "kfo": "application/vnd.kde.kformula",
    "flw": "application/vnd.kde.kivio",
    "kon": "application/vnd.kde.kontour",
    "kpr": "application/vnd.kde.kpresenter",
    "ksp": "application/vnd.kde.kspread",
    "kwd": "application/vnd.kde.kword",
    "htke": "application/vnd.kenameaapp",
    "kia": "application/vnd.kidspiration",
    "kne": "application/vnd.kinar",
    "sse": "application/vnd.kodak-descriptor",
    "lasxml": "application/vnd.las.las+xml",
    "latex": "application/x-latex",
    "lbd": "application/vnd.llamagraphics.life-balance.desktop",
    "lbe": "application/vnd.llamagraphics.life-balance.exchange+xml",
    "jam": "application/vnd.jam",
    "123": "application/vnd.lotus-1-2-3",
    "apr": "application/vnd.lotus-approach",
    "pre": "application/vnd.lotus-freelance",
    "nsf": "application/vnd.lotus-notes",
    "org": "application/vnd.lotus-organizer",
    "scm": "application/vnd.lotus-screencam",
    "lwp": "application/vnd.lotus-wordpro",
    "lvp": "audio/vnd.lucent.voice",
    "m3u": "audio/x-mpegurl",
    "m4v": "video/x-m4v",
    "hqx": "application/mac-binhex40",
    "portpkg": "application/vnd.macports.portpkg",
    "mgp": "application/vnd.osgeo.mapguide.package",
    "mrc": "application/marc",
    "mrcx": "application/marcxml+xml",
    "mxf": "application/mxf",
    "nbp": "application/vnd.wolfram.player",
    "ma": "application/mathematica",
    "mathml": "application/mathml+xml",
    "mbox": "application/mbox",
    "mc1": "application/vnd.medcalcdata",
    "mscml": "application/mediaservercontrol+xml",
    "cdkey": "application/vnd.mediastation.cdkey",
    "mwf": "application/vnd.mfer",
    "mfm": "application/vnd.mfmp",
    "msh": "model/mesh",
    "mads": "application/mads+xml",
    "mets": "application/mets+xml",
    "mods": "application/mods+xml",
    "meta4": "application/metalink4+xml",
    "mcd": "application/vnd.mcd",
    "flo": "application/vnd.micrografx.flo",
    "igx": "application/vnd.micrografx.igx",
    "es3": "application/vnd.eszigno3+xml",
    "mdb": "application/x-msaccess",
    "asf": "video/x-ms-asf",
    "exe": "application/x-msdownload",
    "cil": "application/vnd.ms-artgalry",
    "cab": "application/vnd.ms-cab-compressed",
    "ims": "application/vnd.ms-ims",
    "application": "application/x-ms-application",
    "clp": "application/x-msclip",
    "mdi": "image/vnd.ms-modi",
    "eot": "application/vnd.ms-fontobject",
    "xls": "application/vnd.ms-excel",
    "xlam": "application/vnd.ms-excel.addin.macroenabled.12",
    "xlsb": "application/vnd.ms-excel.sheet.binary.macroenabled.12",
    "xltm": "application/vnd.ms-excel.template.macroenabled.12",
    "xlsm": "application/vnd.ms-excel.sheet.macroenabled.12",
    "chm": "application/vnd.ms-htmlhelp",
    "crd": "application/x-mscardfile",
    "lrm": "application/vnd.ms-lrm",
    "mvb": "application/x-msmediaview",
    "mny": "application/x-msmoney",
    "pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    "sldx": "application/vnd.openxmlformats-officedocument.presentationml.slide",
    "ppsx": "application/vnd.openxmlformats-officedocument.presentationml.slideshow",
    "potx": "application/vnd.openxmlformats-officedocument.presentationml.template",
    "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "xltx": "application/vnd.openxmlformats-officedocument.spreadsheetml.template",
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "dotx": "application/vnd.openxmlformats-officedocument.wordprocessingml.template",
    "obd": "application/x-msbinder",
    "thmx": "application/vnd.ms-officetheme",
    "onetoc": "application/onenote",
    "pya": "audio/vnd.ms-playready.media.pya",
    "pyv": "video/vnd.ms-playready.media.pyv",
    "ppt": "application/vnd.ms-powerpoint",
    "ppam": "application/vnd.ms-powerpoint.addin.macroenabled.12",
    "sldm": "application/vnd.ms-powerpoint.slide.macroenabled.12",
    "pptm": "application/vnd.ms-powerpoint.presentation.macroenabled.12",
    "ppsm": "application/vnd.ms-powerpoint.slideshow.macroenabled.12",
    "potm": "application/vnd.ms-powerpoint.template.macroenabled.12",
    "mpp": "application/vnd.ms-project",
    "pub": "application/x-mspublisher",
    "scd": "application/x-msschedule",
    "xap": "application/x-silverlight-app",
    "stl": "application/vnd.ms-pki.stl",
    "cat": "application/vnd.ms-pki.seccat",
    "vsd": "application/vnd.visio",
    "vsdx": "application/vnd.visio2013",
    "wm": "video/x-ms-wm",
    "wma": "audio/x-ms-wma",
    "wax": "audio/x-ms-wax",
    "wmx": "video/x-ms-wmx",
    "wmd": "application/x-ms-wmd",
    "wpl": "application/vnd.ms-wpl",
    "wmz": "application/x-ms-wmz",
    "wmv": "video/x-ms-wmv",
    "wvx": "video/x-ms-wvx",
    "wmf": "application/x-msmetafile",
    "trm": "application/x-msterminal",
    "doc": "application/msword",
    "docm": "application/vnd.ms-word.document.macroenabled.12",
    "dotm": "application/vnd.ms-word.template.macroenabled.12",
    "wri": "application/x-mswrite",
    "wps": "application/vnd.ms-works",
    "xbap": "application/x-ms-xbap",
    "xps": "application/vnd.ms-xpsdocument",
    "mid": "audio/midi",
    "mpy": "application/vnd.ibm.minipay",
    "afp": "application/vnd.ibm.modcap",
    "rms": "application/vnd.jcp.javame.midlet-rms",
    "tmo": "application/vnd.tmobile-livetv",
    "prc": "application/x-mobipocket-ebook",
    "mbk": "application/vnd.mobius.mbk",
    "dis": "application/vnd.mobius.dis",
    "plc": "application/vnd.mobius.plc",
    "mqy": "application/vnd.mobius.mqy",
    "msl": "application/vnd.mobius.msl",
    "txf": "application/vnd.mobius.txf",
    "daf": "application/vnd.mobius.daf",
    "fly": "text/vnd.fly",
    "mpc": "application/vnd.mophun.certificate",
    "mpn": "application/vnd.mophun.application",
    "mj2": "video/mj2",
    "mpga": "audio/mpeg",
    "mxu": "video/vnd.mpegurl",
    "mpeg": "video/mpeg",
    "m21": "application/mp21",
    "mp4a": "audio/mp4",
    "mp4": "application/mp4",
    "m3u8": "application/vnd.apple.mpegurl",
    "mus": "application/vnd.musician",
    "msty": "application/vnd.muvee.style",
    "mxml": "application/xv+xml",
    "ngdat": "application/vnd.nokia.n-gage.data",
    "n-gage": "application/vnd.nokia.n-gage.symbian.install",
    "ncx": "application/x-dtbncx+xml",
    "nc": "application/x-netcdf",
    "nlu": "application/vnd.neurolanguage.nlu",
    "dna": "application/vnd.dna",
    "nnd": "application/vnd.noblenet-directory",
    "nns": "application/vnd.noblenet-sealer",
    "nnw": "application/vnd.noblenet-web",
    "rpst": "application/vnd.nokia.radio-preset",
    "rpss": "application/vnd.nokia.radio-presets",
    "n3": "text/n3",
    "edm": "application/vnd.novadigm.edm",
    "edx": "application/vnd.novadigm.edx",
    "ext": "application/vnd.novadigm.ext",
    "gph": "application/vnd.flographit",
    "ecelp4800": "audio/vnd.nuera.ecelp4800",
    "ecelp7470": "audio/vnd.nuera.ecelp7470",
    "ecelp9600": "audio/vnd.nuera.ecelp9600",
    "oda": "application/oda",
    "ogx": "application/ogg",
    "oga": "audio/ogg",
    "ogv": "video/ogg",
    "dd2": "application/vnd.oma.dd2+xml",
    "oth": "application/vnd.oasis.opendocument.text-web",
    "opf": "application/oebps-package+xml",
    "qbo": "application/vnd.intu.qbo",
    "oxt": "application/vnd.openofficeorg.extension",
    "osf": "application/vnd.yamaha.openscoreformat",
    "weba": "audio/webm",
    "webm": "video/webm",
    "odc": "application/vnd.oasis.opendocument.chart",
    "otc": "application/vnd.oasis.opendocument.chart-template",
    "odb": "application/vnd.oasis.opendocument.database",
    "odf": "application/vnd.oasis.opendocument.formula",
    "odft": "application/vnd.oasis.opendocument.formula-template",
    "odg": "application/vnd.oasis.opendocument.graphics",
    "otg": "application/vnd.oasis.opendocument.graphics-template",
    "odi": "application/vnd.oasis.opendocument.image",
    "oti": "application/vnd.oasis.opendocument.image-template",
    "odp": "application/vnd.oasis.opendocument.presentation",
    "otp": "application/vnd.oasis.opendocument.presentation-template",
    "ods": "application/vnd.oasis.opendocument.spreadsheet",
    "ots": "application/vnd.oasis.opendocument.spreadsheet-template",
    "odt": "application/vnd.oasis.opendocument.text",
    "odm": "application/vnd.oasis.opendocument.text-master",
    "ott": "application/vnd.oasis.opendocument.text-template",
    "ktx": "image/ktx",
    "sxc": "application/vnd.sun.xml.calc",
    "stc": "application/vnd.sun.xml.calc.template",
    "sxd": "application/vnd.sun.xml.draw",
    "std": "application/vnd.sun.xml.draw.template",
    "sxi": "application/vnd.sun.xml.impress",
    "sti": "application/vnd.sun.xml.impress.template",
    "sxm": "application/vnd.sun.xml.math",
    "sxw": "application/vnd.sun.xml.writer",
    "sxg": "application/vnd.sun.xml.writer.global",
    "stw": "application/vnd.sun.xml.writer.template",
    "otf": "application/x-font-otf",
    "osfpvg": "application/vnd.yamaha.openscoreformat.osfpvg+xml",
    "dp": "application/vnd.osgi.dp",
    "pdb": "application/vnd.palm",
    "p": "text/x-pascal",
    "paw": "application/vnd.pawaafile",
    "pclxl": "application/vnd.hp-pclxl",
    "efif": "application/vnd.picsel",
    "pcx": "image/x-pcx",
    "psd": "image/vnd.adobe.photoshop",
    "prf": "application/pics-rules",
    "pic": "image/x-pict",
    "chat": "application/x-chat",
    "p10": "application/pkcs10",
    "p12": "application/x-pkcs12",
    "p7m": "application/pkcs7-mime",
    "p7s": "application/pkcs7-signature",
    "p7r": "application/x-pkcs7-certreqresp",
    "p7b": "application/x-pkcs7-certificates",
    "p8": "application/pkcs8",
    "plf": "application/vnd.pocketlearn",
    "pnm": "image/x-portable-anymap",
    "pbm": "image/x-portable-bitmap",
    "pcf": "application/x-font-pcf",
    "pfr": "application/font-tdpfr",
    "pgn": "application/x-chess-pgn",
    "pgm": "image/x-portable-graymap",
    "png": "image/x-png",
    "ppm": "image/x-portable-pixmap",
    "pskcxml": "application/pskc+xml",
    "pml": "application/vnd.ctc-posml",
    "ai": "application/postscript",
    "pfa": "application/x-font-type1",
    "pbd": "application/vnd.powerbuilder6",
    "pgp": "application/pgp-signature",
    "box": "application/vnd.previewsystems.box",
    "ptid": "application/vnd.pvi.ptid1",
    "pls": "application/pls+xml",
    "str": "application/vnd.pg.format",
    "ei6": "application/vnd.pg.osasli",
    "dsc": "text/prs.lines.tag",
    "psf": "application/x-font-linux-psf",
    "qps": "application/vnd.publishare-delta-tree",
    "wg": "application/vnd.pmi.widget",
    "qxd": "application/vnd.quark.quarkxpress",
    "esf": "application/vnd.epson.esf",
    "msf": "application/vnd.epson.msf",
    "ssf": "application/vnd.epson.ssf",
    "qam": "application/vnd.epson.quickanime",
    "qfx": "application/vnd.intu.qfx",
    "qt": "video/quicktime",
    "rar": "application/x-rar-compressed",
    "ram": "audio/x-pn-realaudio",
    "rmp": "audio/x-pn-realaudio-plugin",
    "rsd": "application/rsd+xml",
    "rm": "application/vnd.rn-realmedia",
    "bed": "application/vnd.realvnc.bed",
    "mxl": "application/vnd.recordare.musicxml",
    "musicxml": "application/vnd.recordare.musicxml+xml",
    "rnc": "application/relax-ng-compact-syntax",
    "rdz": "application/vnd.data-vision.rdz",
    "rdf": "application/rdf+xml",
    "rp9": "application/vnd.cloanto.rp9",
    "jisp": "application/vnd.jisp",
    "rtf": "application/rtf",
    "rtx": "text/richtext",
    "link66": "application/vnd.route66.link66+xml",
    "rss, .xml": "application/rss+xml",
    "shf": "application/shf+xml",
    "st": "application/vnd.sailingtracker.track",
    "svg": "image/svg+xml",
    "sus": "application/vnd.sus-calendar",
    "sru": "application/sru+xml",
    "setpay": "application/set-payment-initiation",
    "setreg": "application/set-registration-initiation",
    "sema": "application/vnd.sema",
    "semd": "application/vnd.semd",
    "semf": "application/vnd.semf",
    "see": "application/vnd.seemail",
    "snf": "application/x-font-snf",
    "spq": "application/scvp-vp-request",
    "spp": "application/scvp-vp-response",
    "scq": "application/scvp-cv-request",
    "scs": "application/scvp-cv-response",
    "sdp": "application/sdp",
    "etx": "text/x-setext",
    "movie": "video/x-sgi-movie",
    "ifm": "application/vnd.shana.informed.formdata",
    "itp": "application/vnd.shana.informed.formtemplate",
    "iif": "application/vnd.shana.informed.interchange",
    "ipk": "application/vnd.shana.informed.package",
    "tfi": "application/thraud+xml",
    "shar": "application/x-shar",
    "rgb": "image/x-rgb",
    "slt": "application/vnd.epson.salt",
    "aso": "application/vnd.accpac.simply.aso",
    "imp": "application/vnd.accpac.simply.imp",
    "twd": "application/vnd.simtech-mindmapper",
    "csp": "application/vnd.commonspace",
    "saf": "application/vnd.yamaha.smaf-audio",
    "mmf": "application/vnd.smaf",
    "spf": "application/vnd.yamaha.smaf-phrase",
    "teacher": "application/vnd.smart.teacher",
    "svd": "application/vnd.svd",
    "rq": "application/sparql-query",
    "srx": "application/sparql-results+xml",
    "gram": "application/srgs",
    "grxml": "application/srgs+xml",
    "ssml": "application/ssml+xml",
    "skp": "application/vnd.koan",
    "sgml": "text/sgml",
    "sdc": "application/vnd.stardivision.calc",
    "sda": "application/vnd.stardivision.draw",
    "sdd": "application/vnd.stardivision.impress",
    "smf": "application/vnd.stardivision.math",
    "sdw": "application/vnd.stardivision.writer",
    "sgl": "application/vnd.stardivision.writer-global",
    "sm": "application/vnd.stepmania.stepchart",
    "sit": "application/x-stuffit",
    "sitx": "application/x-stuffitx",
    "sdkm": "application/vnd.solent.sdkm+xml",
    "xo": "application/vnd.olpc-sugar",
    "au": "audio/basic",
    "wqd": "application/vnd.wqd",
    "sis": "application/vnd.symbian.install",
    "smi": "application/smil+xml",
    "xsm": "application/vnd.syncml+xml",
    "bdm": "application/vnd.syncml.dm+wbxml",
    "xdm": "application/vnd.syncml.dm+xml",
    "sv4cpio": "application/x-sv4cpio",
    "sv4crc": "application/x-sv4crc",
    "sbml": "application/sbml+xml",
    "tsv": "text/tab-separated-values",
    "tiff": "image/tiff",
    "tao": "application/vnd.tao.intent-module-archive",
    "tar": "application/x-tar",
    "tcl": "application/x-tcl",
    "tex": "application/x-tex",
    "tfm": "application/x-tex-tfm",
    "tei": "application/tei+xml",
    "txt": "text/plain",
    "dxp": "application/vnd.spotfire.dxp",
    "sfs": "application/vnd.spotfire.sfs",
    "tsd": "application/timestamped-data",
    "tpt": "application/vnd.trid.tpt",
    "mxs": "application/vnd.triscape.mxs",
    "t": "text/troff",
    "tra": "application/vnd.trueapp",
    "ttf": "application/x-font-ttf",
    "ttl": "text/turtle",
    "umj": "application/vnd.umajin",
    "uoml": "application/vnd.uoml+xml",
    "unityweb": "application/vnd.unity",
    "ufd": "application/vnd.ufdl",
    "uri": "text/uri-list",
    "utz": "application/vnd.uiq.theme",
    "ustar": "application/x-ustar",
    "uu": "text/x-uuencode",
    "vcs": "text/x-vcalendar",
    "vcf": "text/x-vcard",
    "vcd": "application/x-cdlink",
    "vsf": "application/vnd.vsf",
    "wrl": "model/vrml",
    "vcx": "application/vnd.vcx",
    "mts": "model/vnd.mts",
    "vtu": "model/vnd.vtu",
    "vis": "application/vnd.visionary",
    "viv": "video/vnd.vivo",
    "ccxml": "application/ccxml+xml,",
    "vxml": "application/voicexml+xml",
    "src": "application/x-wais-source",
    "wbxml": "application/vnd.wap.wbxml",
    "wbmp": "image/vnd.wap.wbmp",
    "wav": "audio/x-wav",
    "davmount": "application/davmount+xml",
    "woff": "application/x-font-woff",
    "wspolicy": "application/wspolicy+xml",
    "webp": "image/webp",
    "wtb": "application/vnd.webturbo",
    "wgt": "application/widget",
    "hlp": "application/winhlp",
    "wml": "text/vnd.wap.wml",
    "wmls": "text/vnd.wap.wmlscript",
    "wmlsc": "application/vnd.wap.wmlscriptc",
    "wpd": "application/vnd.wordperfect",
    "stf": "application/vnd.wt.stf",
    "wsdl": "application/wsdl+xml",
    "xbm": "image/x-xbitmap",
    "xpm": "image/x-xpixmap",
    "xwd": "image/x-xwindowdump",
    "der": "application/x-x509-ca-cert",
    "fig": "application/x-xfig",
    "xhtml": "application/xhtml+xml",
    "xml": "application/xml",
    "xdf": "application/xcap-diff+xml",
    "xenc": "application/xenc+xml",
    "xer": "application/patch-ops-error+xml",
    "rl": "application/resource-lists+xml",
    "rs": "application/rls-services+xml",
    "rld": "application/resource-lists-diff+xml",
    "xslt": "application/xslt+xml",
    "xop": "application/xop+xml",
    "xpi": "application/x-xpinstall",
    "xspf": "application/xspf+xml",
    "xul": "application/vnd.mozilla.xul+xml",
    "xyz": "chemical/x-xyz",
    "yaml": "text/yaml",
    "yang": "application/yang",
    "yin": "application/yin+xml",
    "zir": "application/vnd.zul",
    "zip": "application/zip",
    "zmm": "application/vnd.handheld-entertainment+xml",
    "zaz": "application/vnd.zzazz.deck+xml",
}
