from rest_framework import serializers
from .models import LevyBilling, Payment


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Payment
        fields = ["id", "levy_billing", "resident", "amount", "payment_date",
                  "payment_method", "reference", "recorded_by", "created_at"]
        read_only_fields = ["id", "recorded_by", "created_at"]


class LevyBillingSerializer(serializers.ModelSerializer):
    payments = PaymentSerializer(many=True, read_only=True)
    balance  = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model  = LevyBilling
        fields = ["id", "unit", "resident", "billing_month", "amount_due",
                  "due_date", "status", "amount_paid", "balance",
                  "notes", "payments", "created_at"]
        read_only_fields = ["id", "status", "amount_paid", "created_at"]