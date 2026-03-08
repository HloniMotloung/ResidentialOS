from django.conf import settings
from django.db import models
from apps.core.models import TenantModel


class Unit(TenantModel):
    UNIT_TYPES = [
        ("apartment", "Apartment"),
        ("house", "House"),
        ("townhouse", "Townhouse"),
        ("penthouse", "Penthouse"),
    ]

    unit_number         = models.CharField(max_length=20)
    unit_type           = models.CharField(max_length=20, choices=UNIT_TYPES, blank=True)
    bedrooms            = models.PositiveSmallIntegerField(default=1)
    bathrooms           = models.PositiveSmallIntegerField(default=1)
    floor_size_sqm      = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    participation_quota = models.DecimalField(max_digits=6, decimal_places=4, default=0)
    is_occupied         = models.BooleanField(default=False)
    notes               = models.TextField(blank=True)

    class Meta:
        unique_together = ["estate", "unit_number"]
        ordering = ["unit_number"]

    def __str__(self):
        return f"{self.estate.name} — Unit {self.unit_number}"


class Resident(TenantModel):
    TYPE_CHOICES = [
        ("owner", "Owner"),
        ("tenant", "Tenant"),
        ("occupant", "Occupant"),
    ]

    user                   = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name="resident_profiles"
    )
    unit                   = models.ForeignKey(
        Unit, on_delete=models.SET_NULL,
        null=True, blank=True, related_name="residents"
    )
    resident_type          = models.CharField(max_length=20, choices=TYPE_CHOICES)
    first_name             = models.CharField(max_length=100)
    last_name              = models.CharField(max_length=100)
    id_number              = models.CharField(max_length=20, blank=True)
    email                  = models.EmailField()
    phone                  = models.CharField(max_length=20, blank=True)
    emergency_contact_name = models.CharField(max_length=200, blank=True)
    emergency_contact_phone = models.CharField(max_length=20, blank=True)
    move_in_date           = models.DateField(null=True, blank=True)
    move_out_date          = models.DateField(null=True, blank=True)
    is_active              = models.BooleanField(default=True)
    notes                  = models.TextField(blank=True)

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def is_current_resident(self):
        return self.is_active and self.move_out_date is None

    def move_out(self, date):
        self.move_out_date = date
        self.is_active = False
        self.save()
        if self.unit:
            remaining = self.unit.residents.filter(is_active=True).exclude(id=self.id)
            if not remaining.exists():
                self.unit.is_occupied = False
                self.unit.save()

    def __str__(self):
        return f"{self.full_name} ({self.unit})"


class Vehicle(TenantModel):
    resident     = models.ForeignKey(Resident, on_delete=models.CASCADE, related_name="vehicles")
    registration = models.CharField(max_length=20)
    make         = models.CharField(max_length=50, blank=True)
    model        = models.CharField(max_length=50, blank=True)
    colour       = models.CharField(max_length=30, blank=True)
    is_primary   = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.registration} ({self.resident.full_name})"