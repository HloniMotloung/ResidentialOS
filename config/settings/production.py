"""
Production settings for ResidentialOS.
All sensitive values are read from environment variables — never hardcoded.
"""

import os
import dj_database_url
from .base import *  # noqa: F401, F403

# ── CORE ──────────────────────────────────────────────────────────────────────

DEBUG        = False
SECRET_KEY   = os.environ.get("SECRET_KEY")
ALLOWED_HOSTS = os.environ.get("ALLOWED_HOSTS", "").split(",")

# Trust Render's proxy so HTTPS is detected correctly
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# ── DATABASE ──────────────────────────────────────────────────────────────────
# Render injects DATABASE_URL automatically when a Postgres database is linked.

DATABASES = {
    "default": dj_database_url.config(
        env="DATABASE_URL",
        conn_max_age=600,
        ssl_require=True,
    )
}

# ── STATIC FILES (WhiteNoise) ─────────────────────────────────────────────────
# WhiteNoise serves static files directly from Django — no separate nginx needed.

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",   # ← must be second
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "apps.core.middleware.TenantMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"
STATIC_ROOT         = BASE_DIR / "staticfiles"  # noqa: F405

# ── EMAIL (SendGrid) ──────────────────────────────────────────────────────────
# Sign up free at sendgrid.com — free tier gives 100 emails/day.

EMAIL_BACKEND    = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST       = "smtp.sendgrid.net"
EMAIL_PORT       = 587
EMAIL_USE_TLS    = True
EMAIL_HOST_USER  = "apikey"
EMAIL_HOST_PASSWORD = os.environ.get("SENDGRID_API_KEY", "")
DEFAULT_FROM_EMAIL  = os.environ.get("DEFAULT_FROM_EMAIL", "noreply@tloupropertysolutions.co.za")

# ── MEDIA FILES ───────────────────────────────────────────────────────────────
# Render's filesystem is ephemeral — uploaded files disappear on redeploy.
# For now this works for testing. When ready for real use, switch to Cloudinary
# or AWS S3 (see comment below).

MEDIA_URL  = "/media/"
MEDIA_ROOT = BASE_DIR / "media"  # noqa: F405

# ── SECURITY HEADERS ──────────────────────────────────────────────────────────

SECURE_SSL_REDIRECT          = True
SECURE_HSTS_SECONDS          = 31536000   # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD          = True
SECURE_CONTENT_TYPE_NOSNIFF  = True
SESSION_COOKIE_SECURE        = True
CSRF_COOKIE_SECURE           = True
X_FRAME_OPTIONS              = "DENY"

# ── CORS ──────────────────────────────────────────────────────────────────────
# Replace with your actual frontend domain once you have one.

CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOWED_ORIGINS   = os.environ.get("CORS_ALLOWED_ORIGINS", "").split(",")

# ── CELERY ────────────────────────────────────────────────────────────────────
# On the free Render tier, background tasks run eagerly (no Redis needed).
# When you upgrade, set CELERY_BROKER_URL to a Redis URL.

CELERY_BROKER_URL       = os.environ.get("REDIS_URL", "memory://")
CELERY_TASK_ALWAYS_EAGER = not bool(os.environ.get("REDIS_URL"))

# ── LOGGING ───────────────────────────────────────────────────────────────────
# Logs appear in the Render dashboard under "Logs".

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "WARNING",
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": os.environ.get("DJANGO_LOG_LEVEL", "WARNING"),
            "propagate": False,
        },
    },
}
