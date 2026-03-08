from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
                  path("admin/",                    admin.site.urls),

                  # ── Browser interface ──────────────────────────
                  path("",                          include("apps.web.urls")),

                  # ── REST API ───────────────────────────────────
                  path("api/v1/auth/",              include("apps.authentication.urls")),
                  path("api/v1/estates/",           include("apps.estates.urls")),
                  path("api/v1/residents/",         include("apps.residents.urls")),
                  path("api/v1/levies/",            include("apps.levies.urls")),
                  path("api/v1/visitors/",          include("apps.visitors.urls")),
                  path("api/v1/maintenance/",       include("apps.maintenance.urls")),
                  path("api/v1/announcements/",     include("apps.announcements.urls")),
                  path("api/v1/dashboard/",         include("apps.dashboard.urls")),
              ] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)