import uuid
from django.db import models


class TimestampedModel(models.Model):
    """Abstract base — adds created_at / updated_at to every model."""
    id         = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class TenantModel(TimestampedModel):
    """All estate-scoped models inherit this to enforce tenant isolation."""
    estate = models.ForeignKey(
        "estates.Estate",
        on_delete=models.CASCADE,
        related_name="%(class)ss",
    )

    class Meta:
        abstract = True