from django.contrib import admin
from .models import VisitorPreRegistration, GateLog


@admin.register(VisitorPreRegistration)
class VisitorPreRegistrationAdmin(admin.ModelAdmin):
    list_display  = ["visitor_name", "resident", "expected_arrival", "access_code", "is_used"]
    list_filter   = ["is_used", "purpose", "estate"]
    search_fields = ["visitor_name", "access_code"]


@admin.register(GateLog)
class GateLogAdmin(admin.ModelAdmin):
    list_display  = ["visitor_name", "host_resident", "entry_time", "exit_time", "vehicle_registration"]
    list_filter   = ["estate"]
    search_fields = ["visitor_name", "vehicle_registration"]