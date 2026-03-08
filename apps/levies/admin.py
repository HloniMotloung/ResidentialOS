from django.contrib import admin
from .models import LevyRate, LevyBilling, Payment


@admin.register(LevyRate)
class LevyRateAdmin(admin.ModelAdmin):
    list_display  = ["name", "estate", "unit_type", "bedrooms",
                     "min_size_sqm", "max_size_sqm", "amount",
                     "effective_from", "effective_to", "is_active"]
    list_filter   = ["estate", "unit_type", "is_active"]
    search_fields = ["name", "notes"]

    fieldsets = (
        ("Rate Details", {
            "fields": ("estate", "name", "amount", "is_active")
        }),
        ("Applies To — Unit Type", {
            "description": "Leave blank to apply to all unit types.",
            "fields": ("unit_type", "bedrooms")
        }),
        ("Applies To — Size Range", {
            "description": "Leave both blank if size does not affect this rate.",
            "fields": ("min_size_sqm", "max_size_sqm")
        }),
        ("Effective Period", {
            "fields": ("effective_from", "effective_to")
        }),
        ("Notes", {
            "fields": ("notes",)
        }),
    )


@admin.register(LevyBilling)
class LevyBillingAdmin(admin.ModelAdmin):
    list_display  = ["unit", "billing_month", "levy_rate",
                     "amount_due", "amount_paid", "status"]
    list_filter   = ["status", "billing_month", "estate"]
    search_fields = ["unit__unit_number"]


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display  = ["resident", "amount", "payment_date",
                     "payment_method", "reference"]
    list_filter   = ["payment_method", "estate"]
    search_fields = ["resident__first_name", "resident__last_name", "reference"]