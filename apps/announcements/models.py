from django.conf import settings
from django.db import models
from django.utils import timezone
from apps.core.models import TenantModel


class Announcement(TenantModel):
    CATEGORY = [
        ("general",     "General"),
        ("urgent",      "Urgent"),
        ("maintenance", "Maintenance"),
        ("financial",   "Financial"),
    ]

    created_by   = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    title        = models.CharField(max_length=300)
    body         = models.TextField()
    category     = models.CharField(max_length=50, choices=CATEGORY, default="general")
    is_published = models.BooleanField(default=False)
    published_at = models.DateTimeField(null=True, blank=True)
    expires_at   = models.DateTimeField(null=True, blank=True)
    send_email   = models.BooleanField(default=True)
    send_sms     = models.BooleanField(default=False)
    attachment   = models.CharField(max_length=500, blank=True)

    @property
    def is_active(self):
        if not self.is_published:
            return False
        if self.expires_at and timezone.now() > self.expires_at:
            return False
        return True

    def publish(self):
        self.is_published = True
        self.published_at = timezone.now()
        self.save()

    def __str__(self):
        return self.title