from django.conf import settings
from django.db import models
from django.utils import timezone
from apps.core.models import TenantModel
from apps.residents.models import Unit, Resident


class MaintenanceRequest(TenantModel):
    PRIORITY = [("low","Low"), ("medium","Medium"), ("high","High"), ("critical","Critical")]
    STATUS   = [("open","Open"), ("in_progress","In Progress"), ("on_hold","On Hold"),
                ("resolved","Resolved"), ("closed","Closed")]
    CATEGORY = [("plumbing","Plumbing"), ("electrical","Electrical"), ("structural","Structural"),
                ("appliance","Appliance"), ("general","General"), ("security","Security")]

    unit           = models.ForeignKey(Unit, on_delete=models.PROTECT, related_name="maintenance_requests")
    reported_by    = models.ForeignKey(Resident, on_delete=models.PROTECT, related_name="maintenance_requests")
    title          = models.CharField(max_length=200)
    description    = models.TextField()
    category       = models.CharField(max_length=50, choices=CATEGORY, default="general")
    priority       = models.CharField(max_length=20, choices=PRIORITY, default="medium")
    status         = models.CharField(max_length=20, choices=STATUS, default="open")
    assigned_to    = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name="assigned_maintenance"
    )
    assigned_at    = models.DateTimeField(null=True, blank=True)
    resolved_at    = models.DateTimeField(null=True, blank=True)
    estimated_cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    actual_cost    = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    attachments    = models.JSONField(default=list)  # List of S3 paths

    def assign(self, user):
        self.assigned_to = user
        self.assigned_at = timezone.now()
        self.status = "in_progress"
        self.save()

    def resolve(self, cost=None):
        self.status = "resolved"
        self.resolved_at = timezone.now()
        if cost is not None:
            self.actual_cost = cost
        self.save()

    def __str__(self):
        return f"[{self.get_priority_display()}] {self.title} — {self.unit}"


class MaintenanceComment(TenantModel):
    request     = models.ForeignKey(MaintenanceRequest, on_delete=models.CASCADE, related_name="comments")
    author      = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    comment     = models.TextField()
    is_internal = models.BooleanField(default=False)  # Hidden from resident if True

    def __str__(self):
        return f"Comment by {self.author} on {self.request}"