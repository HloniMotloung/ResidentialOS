from rest_framework import serializers
from .models import Estate


class EstateSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Estate
        fields = [
            "id", "name", "slug", "address",
            "contact_email", "contact_phone",
            "is_active", "subscription_plan",
            "monthly_levy_amount", "late_penalty_percent",
            "levy_due_day", "currency",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]