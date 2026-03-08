from rest_framework import serializers
from .models import VisitorPreRegistration, GateLog


class VisitorPreRegistrationSerializer(serializers.ModelSerializer):
    is_valid = serializers.BooleanField(read_only=True)

    class Meta:
        model  = VisitorPreRegistration
        fields = ["id", "resident", "visitor_name", "visitor_id_number",
                  "visitor_phone", "expected_arrival", "expected_departure",
                  "purpose", "access_code", "is_used", "expires_at",
                  "is_valid", "created_at"]
        read_only_fields = ["id", "access_code", "is_used", "expires_at", "created_at"]


class GateLogSerializer(serializers.ModelSerializer):
    is_inside        = serializers.BooleanField(read_only=True)
    duration_minutes = serializers.IntegerField(read_only=True)

    class Meta:
        model  = GateLog
        fields = ["id", "pre_registration", "visitor_name", "visitor_id_number",
                  "vehicle_registration", "host_resident", "entry_time",
                  "exit_time", "security_officer", "notes",
                  "is_inside", "duration_minutes", "created_at"]
        read_only_fields = ["id", "entry_time", "security_officer", "created_at"]