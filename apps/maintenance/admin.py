from django.contrib import admin
from .models import MaintenanceRequest, MaintenanceComment


@admin.register(MaintenanceRequest)
class MaintenanceRequestAdmin(admin.ModelAdmin):
    list_display  = ["title", "unit", "priority", "status", "assigned_to", "created_at"]
    list_filter   = ["priority", "status", "category", "estate"]
    search_fields = ["title", "description"]


@admin.register(MaintenanceComment)
class MaintenanceCommentAdmin(admin.ModelAdmin):
    list_display  = ["request", "author", "is_internal", "created_at"]
    list_filter   = ["is_internal"]