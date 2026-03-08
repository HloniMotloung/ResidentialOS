from rest_framework import serializers
from .models import Unit, Resident


class UnitSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Unit
        fields = ["id", "unit_number", "unit_type", "bedrooms", "bathrooms",
                  "floor_size_sqm", "is_occupied", "participation_quota", "notes"]
        read_only_fields = ["id"]


class ResidentSerializer(serializers.ModelSerializer):
    unit_detail = UnitSerializer(source="unit", read_only=True)
    full_name   = serializers.SerializerMethodField()

    class Meta:
        model  = Resident
        fields = ["id", "first_name", "last_name", "full_name", "email",
                  "phone", "resident_type", "unit", "unit_detail",
                  "move_in_date", "move_out_date", "is_active",
                  "id_number", "notes", "created_at"]
        read_only_fields = ["id", "created_at"]

    def get_full_name(self, obj):
        return obj.full_name

    def validate(self, data):
        unit   = data.get("unit")
        estate = self.context["request"].estate
        if unit and unit.estate != estate:
            raise serializers.ValidationError("Unit does not belong to this estate.")
        return data