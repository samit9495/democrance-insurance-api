"""Payment records for the simulated gateway (REQUIREMENTS 6.7).

A payment is an immutable-once-settled receipt: it captures the amount and
currency copied from the policy at the moment of payment, the method taken, and
an optional ``idempotency_key`` so a retried request cannot charge twice.
"""

from __future__ import annotations

import uuid

from django.db import models

from apps.common.models import TimeStampedModel


class Payment(TimeStampedModel):
    class Method(models.TextChoices):
        CARD = "simulated_card", "Simulated card"
        INVOICE = "invoice", "Invoice"

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        SUCCEEDED = "succeeded", "Succeeded"
        FAILED = "failed", "Failed"

    reference = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    policy = models.ForeignKey("policies.Policy", on_delete=models.PROTECT, related_name="payments")
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3)
    method = models.CharField(max_length=20, choices=Method.choices)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    # unique but nullable: keyless payments store NULL and never collide.
    idempotency_key = models.CharField(  # noqa: DJ001
        max_length=255, unique=True, null=True, blank=True
    )
    provider_payload = models.JSONField(default=dict, blank=True)
    settled_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ("-created_at", "-id")
        indexes = [models.Index(fields=["policy", "status"])]

    def __str__(self) -> str:
        return f"{self.reference} {self.method} {self.amount} {self.currency} ({self.status})"
