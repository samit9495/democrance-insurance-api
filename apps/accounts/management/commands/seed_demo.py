"""Seed demo principals and one linked customer so a reviewer can log in at once.

Idempotent: re-running updates in place rather than duplicating. Passwords are
fixed demo values and are printed, because this command only exists for the demo
(never run it against a real deployment).
"""

from __future__ import annotations

import datetime

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction

DEMO_PASSWORD = "demo-pass-123"

PRINCIPALS = [
    ("staff@demo.local", "staff", {"is_staff": True}),
    ("agent@demo.local", "agent", {}),
    ("customer@demo.local", "customer", {}),
]


class Command(BaseCommand):
    help = "Create demo staff/agent/customer principals and a linked demo customer."

    @transaction.atomic
    def handle(self, *args, **options):
        User = get_user_model()

        users = {}
        for email, role, extra in PRINCIPALS:
            user, _ = User.objects.update_or_create(
                email=email, defaults={"role": role, "is_active": True, **extra}
            )
            user.set_password(DEMO_PASSWORD)
            user.save()
            users[role] = user

        # Link the customer principal to a real Customer business record.
        from apps.customers.models import Customer

        customer, _ = Customer.objects.update_or_create(
            email="customer@demo.local",
            defaults={
                "first_name": "Demo",
                "last_name": "Customer",
                "dob": datetime.date(1991, 6, 25),
                "user": users["customer"],
            },
        )

        self.stdout.write(
            self.style.SUCCESS(
                f"Seeded demo principals (password '{DEMO_PASSWORD}') and "
                f"customer #{customer.id} linked to customer@demo.local."
            )
        )
