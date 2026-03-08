from decimal import Decimal
from django.conf import settings
from django.db import models
from django.utils import timezone
from apps.core.models import TenantModel
from apps.residents.models import Unit, Resident


class LevyRate(TenantModel):
    """
    Defines the levy amount for a specific unit type or size range
    within an estate. The system will use the most specific match
    when generating monthly bills.
    """
    UNIT_TYPES = [
        ("apartment",  "Apartment"),
        ("house",      "House"),
        ("townhouse",  "Townhouse"),
        ("penthouse",  "Penthouse"),
        ("studio",     "Studio"),
        ("commercial", "Commercial"),
        ("other",      "Other"),
    ]

    name             = models.CharField(
        max_length=100,
        help_text="e.g. '2 Bedroom Apartment' or 'Large House'"
    )
    unit_type        = models.CharField(
        max_length=20,
        choices=UNIT_TYPES,
        blank=True,
        help_text="Leave blank to apply to all unit types"
    )
    min_size_sqm     = models.DecimalField(
        max_digits=8, decimal_places=2,
        null=True, blank=True,
        help_text="Minimum floor size in m² (leave blank for no minimum)"
    )
    max_size_sqm     = models.DecimalField(
        max_digits=8, decimal_places=2,
        null=True, blank=True,
        help_text="Maximum floor size in m² (leave blank for no maximum)"
    )
    bedrooms         = models.PositiveSmallIntegerField(
        null=True, blank=True,
        help_text="Number of bedrooms (leave blank to apply to all)"
    )
    amount           = models.DecimalField(
        max_digits=10, decimal_places=2,
        help_text="Monthly levy amount in ZAR"
    )
    is_active        = models.BooleanField(default=True)
    effective_from   = models.DateField(
        help_text="Date this rate comes into effect"
    )
    effective_to     = models.DateField(
        null=True, blank=True,
        help_text="Leave blank if this rate has no end date"
    )
    notes            = models.TextField(
        blank=True,
        help_text="Internal notes about this rate"
    )

    class Meta:
        ordering = ["unit_type", "min_size_sqm", "bedrooms"]

    def __str__(self):
        return f"{self.estate.name} — {self.name} — R{self.amount}/month"

    def matches_unit(self, unit):
        """
        Returns True if this rate applies to the given unit.
        Checks unit_type, bedrooms, and floor size range.
        """
        if self.unit_type and unit.unit_type != self.unit_type:
            return False
        if self.bedrooms is not None and unit.bedrooms != self.bedrooms:
            return False
        if self.min_size_sqm is not None and unit.floor_size_sqm is not None:
            if unit.floor_size_sqm < self.min_size_sqm:
                return False
        if self.max_size_sqm is not None and unit.floor_size_sqm is not None:
            if unit.floor_size_sqm > self.max_size_sqm:
                return False
        return True


class LevyBilling(TenantModel):
    STATUS = [
        ("outstanding", "Outstanding"),
        ("partial",     "Partial"),
        ("paid",        "Paid"),
        ("overdue",     "Overdue"),
    ]

    unit          = models.ForeignKey(Unit, on_delete=models.PROTECT, related_name="levy_billings")
    resident      = models.ForeignKey(Resident, on_delete=models.SET_NULL, null=True, related_name="levy_billings")
    levy_rate     = models.ForeignKey(LevyRate, on_delete=models.SET_NULL,
                                      null=True, blank=True,
                                      help_text="The rate that was applied for this billing")
    billing_month = models.DateField()
    amount_due    = models.DecimalField(max_digits=12, decimal_places=2)
    due_date      = models.DateField()
    status        = models.CharField(max_length=20, choices=STATUS, default="outstanding")
    amount_paid   = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    notes         = models.TextField(blank=True)

    @property
    def balance(self):
        return self.amount_due - self.amount_paid

    def update_status(self):
        if self.amount_paid >= self.amount_due:
            self.status = "paid"
        elif self.amount_paid > 0:
            self.status = "partial"
        elif timezone.now().date() > self.due_date:
            self.status = "overdue"
        else:
            self.status = "outstanding"
        self.save(update_fields=["status"])

    class Meta:
        unique_together = ["unit", "billing_month"]
        ordering        = ["-billing_month"]

    def __str__(self):
        return f"{self.unit} — {self.billing_month:%b %Y} — R{self.amount_due}"


class Payment(TenantModel):
    METHOD_CHOICES = [
        ("eft",          "EFT / Bank Transfer"),
        ("cash",         "Cash"),
        ("debit_order",  "Debit Order"),
        ("card",         "Card"),
    ]

    levy_billing   = models.ForeignKey(LevyBilling, on_delete=models.PROTECT, related_name="payments")
    resident       = models.ForeignKey(Resident, on_delete=models.PROTECT)
    amount         = models.DecimalField(max_digits=12, decimal_places=2)
    payment_date   = models.DateField()
    payment_method = models.CharField(max_length=20, choices=METHOD_CHOICES, default="eft")
    reference      = models.CharField(max_length=100, blank=True)
    recorded_by    = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    proof_document = models.CharField(max_length=500, blank=True)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        from django.db.models import Sum
        billing       = self.levy_billing
        total         = billing.payments.aggregate(total=Sum("amount"))["total"] or Decimal("0.00")
        billing.amount_paid = total
        billing.save(update_fields=["amount_paid"])
        billing.update_status()

    def __str__(self):
        return f"R{self.amount} — {self.resident.full_name} — {self.payment_date}"