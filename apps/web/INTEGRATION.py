# Web Interface Integration Instructions
# ==========================================
# Add the following changes to your existing project files:

# ── 1. config/settings/base.py ────────────────────────────────
# Add 'apps.web' to LOCAL_APPS:
#
# LOCAL_APPS = [
#     "apps.core",
#     "apps.authentication",
#     "apps.estates",
#     "apps.residents",
#     "apps.levies",
#     "apps.visitors",
#     "apps.maintenance",
#     "apps.announcements",
#     "apps.dashboard",
#     "apps.notifications",
#     "apps.web",             # ← ADD THIS
# ]
#
# Add TEMPLATES setting (if not already present):
# TEMPLATES = [
#     {
#         "BACKEND": "django.template.backends.django.DjangoTemplates",
#         "DIRS": [BASE_DIR / "templates"],
#         "APP_DIRS": True,
#         "OPTIONS": {
#             "context_processors": [
#                 "django.template.context_processors.debug",
#                 "django.template.context_processors.request",
#                 "django.contrib.auth.context_processors.auth",
#                 "django.contrib.messages.context_processors.messages",
#             ],
#         },
#     },
# ]
#
# Add STATICFILES_DIRS (if not already present):
# STATICFILES_DIRS = [BASE_DIR / "static"]
#
# Add LOGIN_URL:
# LOGIN_URL = "/"


# ── 2. config/urls.py ────────────────────────────────────────
# Add the web URLs BEFORE the API urls and change the root:
#
# from django.conf import settings
# from django.conf.urls.static import static
# from django.contrib import admin
# from django.urls import path, include
#
# urlpatterns = [
#     path("admin/",               admin.site.urls),
#
#     # Browser interface  ← ADD THIS BLOCK
#     path("",                     include("apps.web.urls")),
#
#     # REST API
#     path("api/v1/auth/",         include("apps.authentication.urls")),
#     path("api/v1/estates/",      include("apps.estates.urls")),
#     path("api/v1/residents/",    include("apps.residents.urls")),
#     path("api/v1/levies/",       include("apps.levies.urls")),
#     path("api/v1/visitors/",     include("apps.visitors.urls")),
#     path("api/v1/maintenance/",  include("apps.maintenance.urls")),
#     path("api/v1/announcements/",include("apps.announcements.urls")),
#     path("api/v1/dashboard/",    include("apps.dashboard.urls")),
# ] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
