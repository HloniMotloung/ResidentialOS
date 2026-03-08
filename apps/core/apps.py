from django.apps import AppConfig

class CoreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.core"

    def ready(self):
        from django.contrib import admin
        admin.site.site_header = "Tlou Property Solutions"
        admin.site.site_title  = "Tlou Property Solutions"
        admin.site.index_title = "Admin Panel"