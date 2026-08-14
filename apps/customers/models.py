"""Customer master data (REQUIREMENTS 6.2)."""

from __future__ import annotations

import datetime
import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from apps.common.models import TimeStampedModel


class Customer(TimeStampedModel):
    # Integer PK because the diagram uses "customer_id": 1.
    reference = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)

    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    dob = models.DateField()

    email = models.EmailField(null=True, blank=True, unique=True)
    phone = models.CharField(max_length=32, blank=True)

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="customer_profile",
    )

    class Meta:
        ordering = ("last_name", "first_name", "id")
        indexes = [
            models.Index(fields=["last_name", "first_name"]),
            models.Index(fields=["dob"]),
        ]

    def __str__(self) -> str:
        return f"{self.first_name} {self.last_name}"

    def age_at(self, as_of: datetime.date) -> int:
        """Whole years old on ``as_of``, correct at the birthday boundary."""
        born = self.dob
        had_birthday = (as_of.month, as_of.day) >= (born.month, born.day)
        return as_of.year - born.year - (0 if had_birthday else 1)

    @property
    def age(self) -> int:
        return self.age_at(timezone.localdate())

    def clean(self) -> None:
        super().clean()
        if self.dob is None:
            return
        today = timezone.localdate()
        if self.dob >= today:
            raise ValidationError({"dob": "Date of birth must be in the past."})
        min_age = getattr(settings, "CUSTOMER_MIN_AGE", 18)
        max_age = getattr(settings, "CUSTOMER_MAX_AGE", 100)
        age = self.age_at(today)
        if not (min_age <= age <= max_age):
            raise ValidationError({"dob": f"Customer age must be between {min_age} and {max_age}."})
