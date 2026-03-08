import random
import string
from datetime import timedelta
from django.conf import settings
from django.db import models
from django.utils import timezone
from apps.core.models import TenantModel
from apps.residents.models import Resident


def generate_access_code():
    return "".join(random.choices(string.digits, k=6))


class VisitorPreRegistration(TenantModel):
    PURPOSE = [
        ("social", "Social Visit"),
        ("delivery", "Delivery"),
        ("contractor", "Contractor"),
        ("service", "Service Provider"),
    ]

    resident           = models.ForeignKey(Resident, on_delete=models.CASCADE, related_name="visitor_invitations")
    visitor_name       = models.CharField(max_length=200)
    visitor_id_number  = models.CharField(max_length=20, blank=True)
    visitor_phone      = models.CharField(max_length=20, blank=True)
    expected_arrival   = models.DateTimeField()
    expected_departure = models.DateTimeField(null=True, blank=True)
    purpose            = models.CharField(max_length=50, choices=PURPOSE, default="social")
    access_code        = models.CharField(max_length=10, unique=True, default=generate_access_code)
    is_used            = models.BooleanField(default=False)
    expires_at         = models.DateTimeField()

    def save(self, *args, **kwargs):
        if not self.expires_at:
            self.expires_at = self.expected_arrival + timedelta(hours=24)
        super().save(*args, **kwargs)

    @property
    def is_valid(self):
        return not self.is_used and timezone.now() < self.expires_at

    def __str__(self):
        return f"{self.visitor_name} → {self.resident.full_name} ({self.access_code})"


class GateLog(TenantModel):
    pre_registration     = models.ForeignKey(
        VisitorPreRegistration, on_delete=models.SET_NULL,
        null=True, blank=True, related_name="gate_logs"
    )
    visitor_name         = models.CharField(max_length=200)
    visitor_id_number    = models.CharField(max_length=20, blank=True)
    vehicle_registration = models.CharField(max_length=20, blank=True)
    host_resident        = models.ForeignKey(Resident, on_delete=models.SET_NULL, null=True, blank=True)
    entry_time           = models.DateTimeField(auto_now_add=True)
    exit_time            = models.DateTimeField(null=True, blank=True)
    security_officer     = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )
    notes                = models.TextField(blank=True)

    @property
    def is_inside(self):
        return self.exit_time is None

    @property
    def duration_minutes(self):
        if self.exit_time:
            return int((self.exit_time - self.entry_time).total_seconds() / 60)
        return None

    def log_exit(self):
        self.exit_time = timezone.now()
        self.save(update_fields=["exit_time"])

    def __str__(self):
        return f"{self.visitor_name} — {self.entry_time:%Y-%m-%d %H:%M}"