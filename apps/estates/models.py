from django.db import models
from apps.core.models import TimestampedModel


class Estate(TimestampedModel):
    PLAN_CHOICES = [
        ("starter",      "Starter"),
        ("professional", "Professional"),
        ("enterprise",   "Enterprise"),
    ]

    name                 = models.CharField(max_length=200)
    slug                 = models.SlugField(max_length=100, unique=True)
    schema_name          = models.CharField(max_length=100, unique=True)
    address              = models.TextField(blank=True)
    contact_email        = models.EmailField()
    contact_phone        = models.CharField(max_length=20, blank=True)
    is_active            = models.BooleanField(default=True)
    subscription_plan    = models.CharField(max_length=50, choices=PLAN_CHOICES, default="starter")

    # ── Replacing config JSONField with plain fields ──────────────
    monthly_levy_amount  = models.DecimalField(
        max_digits=10, decimal_places=2,
        default=0,
        help_text="Monthly levy amount charged to each unit (ZAR)"
    )
    late_penalty_percent = models.DecimalField(
        max_digits=5, decimal_places=2,
        default=0,
        help_text="Penalty percentage applied to overdue accounts"
    )
    levy_due_day         = models.PositiveSmallIntegerField(
        default=1,
        help_text="Day of the month levies are due (1-28)"
    )
    currency             = models.CharField(
        max_length=10,
        default="ZAR",
        help_text="Currency code e.g. ZAR, USD"
    )

    def __str__(self):
        return self.name