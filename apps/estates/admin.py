from django.contrib import admin
from .models import Estate


@admin.register(Estate)
class EstateAdmin(admin.ModelAdmin):
    list_display = ["name", "slug", "subscription_plan", "is_active",
                    "monthly_levy_amount", "created_at"]
    search_fields       = ["name", "slug"]
    list_filter         = ["subscription_plan", "is_active"]
    prepopulated_fields = {"slug": ("name",), "schema_name": ("name",)}

    fieldsets = (
        ("Basic Information", {
            "fields": (
                "name",
                "slug",
                "schema_name",
                "address",
                "is_active",
                "subscription_plan",
            )
        }),
        ("Contact Details", {
            "fields": (
                "contact_email",
                "contact_phone",
            )
        }),
        ("Financial Settings", {
            "fields": (
                "monthly_levy_amount",
                "late_penalty_percent",
                "levy_due_day",
                "currency",
            )
        }),
    )