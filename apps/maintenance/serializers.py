from rest_framework import serializers
from .models import MaintenanceRequest, MaintenanceComment


class MaintenanceCommentSerializer(serializers.ModelSerializer):
    author_name = serializers.CharField(source="author.get_full_name", read_only=True)

    class Meta:
        model  = MaintenanceComment
        fields = ["id", "request", "author", "author_name", "comment",
                  "is_internal", "created_at"]
        read_only_fields = ["id", "author", "created_at"]


class MaintenanceRequestSerializer(serializers.ModelSerializer):
    comments         = MaintenanceCommentSerializer(many=True, read_only=True)
    reported_by_name = serializers.CharField(source="reported_by.full_name", read_only=True)
    assigned_to_name = serializers.CharField(source="assigned_to.get_full_name", read_only=True)

    class Meta:
        model  = MaintenanceRequest
        fields = ["id", "unit", "reported_by", "reported_by_name", "title",
                  "description", "category", "priority", "status",
                  "assigned_to", "assigned_to_name", "assigned_at",
                  "resolved_at", "estimated_cost", "actual_cost",
                  "attachments", "comments", "created_at"]
        read_only_fields = ["id", "assigned_at", "resolved_at", "created_at"]