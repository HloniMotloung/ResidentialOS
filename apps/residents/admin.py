from django.contrib import admin
from .models import Unit, Resident


@admin.register(Unit)
class UnitAdmin(admin.ModelAdmin):
    list_display  = ["unit_number", "estate", "unit_type", "bedrooms", "is_occupied"]
    list_filter   = ["is_occupied", "unit_type", "estate"]
    search_fields = ["unit_number"]


@admin.register(Resident)
class ResidentAdmin(admin.ModelAdmin):
    list_display  = ["full_name", "estate", "unit", "resident_type", "is_active"]
    list_filter   = ["resident_type", "is_active", "estate"]
    search_fields = ["first_name", "last_name", "email"]