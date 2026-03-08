import os
from pathlib import Path
from decouple import config

BASE_DIR = Path(__file__).resolve().parent.parent.parent

SECRET_KEY = config("SECRET_KEY", default="change-me-in-production")

DEBUG = config("DEBUG", default=True, cast=bool)

ALLOWED_HOSTS = config("ALLOWED_HOSTS", default="*").split(",")

DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

THIRD_PARTY_APPS = [
    "rest_framework",
    "rest_framework_simplejwt",
    "django_filters",
    "corsheaders",
]

LOCAL_APPS = [
    "apps.authentication",
    "apps.core",
    "apps.estates",
    "apps.residents",
    "apps.levies",
    "apps.visitors",
    "apps.maintenance",
    "apps.announcements",
    "apps.dashboard",
    "apps.notifications",
    "apps.web",
]

INSTALLED_APPS = DJANGO_APPS + [
    "rest_framework_simplejwt.token_blacklist",
] + THIRD_PARTY_APPS + LOCAL_APPS

ADMIN_SITE_HEADER  = "Tlou Property Solutions"
ADMIN_SITE_TITLE   = "Tlou Property Solutions"
ADMIN_INDEX_TITLE  = "Admin Panel"

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "apps.core.middleware.TenantMiddleware",          # Our custom tenant resolver
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [{
    "BACKEND": "django.template.backends.django.DjangoTemplates",
    "DIRS": [BASE_DIR / "templates"],
    "APP_DIRS": True,
    "OPTIONS": {"context_processors": [
        "django.template.context_processors.request",
        "django.contrib.auth.context_processors.auth",
        "django.contrib.messages.context_processors.messages",
    ]},
}]

STATICFILES_DIRS = [BASE_DIR / "static"]
LOGIN_URL = "/"

WSGI_APPLICATION = "config.wsgi.application"



AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE     = "Africa/Johannesburg"
USE_I18N      = True
USE_TZ        = True

STATIC_URL  = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_URL   = "/media/"
MEDIA_ROOT  = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

AUTH_USER_MODEL = "authentication.User"

# ── Django REST Framework ──────────────────────────────────────────
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
}

# ── JWT ────────────────────────────────────────────────────────────
from datetime import timedelta

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME":  timedelta(hours=8),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=30),
    "ROTATE_REFRESH_TOKENS":  True,
}

# ── CORS ───────────────────────────────────────────────────────────
CORS_ALLOW_ALL_ORIGINS = True   # Tighten this in production

# ── Email (console backend for dev) ───────────────────────────────
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
DEFAULT_FROM_EMAIL = "noreply@residentialos.com"

# ── Celery ─────────────────────────────────────────────────────────
CELERY_TIMEZONE               = TIME_ZONE
CELERY_TASK_TRACK_STARTED     = True
CELERY_TASK_TIME_LIMIT        = 30 * 60