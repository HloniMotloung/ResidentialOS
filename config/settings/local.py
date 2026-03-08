from .base import *

DEBUG = True

# ── SQLite — zero setup needed ─────────────────────────────────────
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME":   BASE_DIR / "db.sqlite3",
    }
}

# ── Celery — run tasks eagerly (no Redis needed in dev) ────────────
# Tasks execute immediately inline instead of being queued.
# Set to False once you install Redis locally.
# Run Celery tasks synchronously — no broker needed in local dev
CELERY_TASK_ALWAYS_EAGER  = True
CELERY_EAGER_PROPAGATES   = True
CELERY_BROKER_URL         = 'memory://'

# ── Email — print emails to terminal instead of sending ────────────
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# ── CORS — allow all in dev ────────────────────────────────────────
CORS_ALLOW_ALL_ORIGINS = True

# ── Django Debug Toolbar (optional, install separately) ────────────
# pip install django-debug-toolbar
# INSTALLED_APPS += ["debug_toolbar"]
# MIDDLEWARE    += ["debug_toolbar.middleware.DebugToolbarMiddleware"]
# INTERNAL_IPS   = ["127.0.0.1"]