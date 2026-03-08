from rest_framework import serializers
from .models import Announcement


class AnnouncementSerializer(serializers.ModelSerializer):
    created_by_name = serializers.CharField(source="created_by.get_full_name", read_only=True)
    is_active       = serializers.BooleanField(read_only=True)

    class Meta:
        model  = Announcement
        fields = ["id", "created_by", "created_by_name", "title", "body",
                  "category", "is_published", "published_at", "expires_at",
                  "send_email", "send_sms", "attachment", "is_active", "created_at"]
        read_only_fields = ["id", "created_by", "published_at", "created_at"]