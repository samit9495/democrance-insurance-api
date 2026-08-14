"""Policy and its append-only state history (REQUIREMENTS 6.5/6.6, D7)."""

from __future__ import annotations

import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone

from apps.common.models import TimeStampedModel
from apps.policies.state_machine import CHOICES, State


def generate_quote_reference() -> str:
    return f"QT-{timezone.now():%Y}-{uuid.uuid4().hex[:8].upper()}"


class Policy(TimeStampedModel):
    quote_reference = models.CharField(
        max_length=32, unique=True, default=generate_quote_reference, editable=False
    )

    customer = models.ForeignKey(
        "customers.Customer", on_delete=models.PROTECT, related_name="policies"
    )
    product = models.ForeignKey(
        "products.ProductType", on_delete=models.PROTECT, related_name="policies"
    )

    premium = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    cover = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3)

    state = models.CharField(max_length=20, choices=CHOICES, default=State.NEW)

    rating_rule = models.ForeignKey(
        "products.RatingRule", on_delete=models.SET_NULL, null=True, blank=True
    )
    rated_age = models.PositiveSmallIntegerField(null=True, blank=True)
    rated_at = models.DateTimeField(null=True, blank=True)

    quoted_at = models.DateTimeField(null=True, blank=True)
    accepted_at = models.DateTimeField(null=True, blank=True)
    activated_at = models.DateTimeField(null=True, blank=True)
    quote_expires_at = models.DateTimeField(null=True, blank=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )

    class Meta:
        ordering = ("-created_at", "-id")
        indexes = [
            models.Index(fields=["customer", "state"]),
            models.Index(fields=["state"]),
            models.Index(fields=["created_at"]),
        ]
        verbose_name_plural = "policies"

    def __str__(self) -> str:
        return f"{self.quote_reference} ({self.state})"

    @property
    def is_expired(self) -> bool:
        return self.quote_expires_at is not None and timezone.now() > self.quote_expires_at


class PolicyStateTransition(TimeStampedModel):
    SOURCE_CHOICES = [("api", "API"), ("admin", "Admin"), ("system", "System")]

    policy = models.ForeignKey(Policy, on_delete=models.CASCADE, related_name="transitions")
    # NULL (not "") is intentional: the genesis "-> new" transition has no origin.
    from_state = models.CharField(max_length=20, null=True, blank=True)  # noqa: DJ001
    to_state = models.CharField(max_length=20)
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )
    source = models.CharField(max_length=10, choices=SOURCE_CHOICES, default="system")
    reason = models.CharField(max_length=255, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ("created_at", "id")
        indexes = [models.Index(fields=["policy", "created_at"])]

    def __str__(self) -> str:
        return f"{self.policy_id}: {self.from_state} -> {self.to_state}"

    def save(self, *args, **kwargs):
        # History that can be edited is not history: writes are allowed once.
        if self.pk is not None:
            raise ValueError("PolicyStateTransition is immutable and cannot be modified.")
        super().save(*args, **kwargs)
