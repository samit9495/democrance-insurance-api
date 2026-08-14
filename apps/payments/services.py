"""Payment simulation, wired atomically into policy activation (domain-invariants).

``simulate_payment`` is the single entry point. It locks the policy row, honours
the ``Idempotency-Key`` contract, records a :class:`Payment`, and binds the
policy (``accepted -> active``) in the SAME transaction, so a policy is never
active without a payment and a payment never exists without binding its policy.
"""

from __future__ import annotations

import logging

from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from apps.payments.exceptions import DuplicateRequest, PaymentNotAllowed
from apps.payments.models import Payment
from apps.policies.models import Policy
from apps.policies.services import activate_policy
from apps.policies.state_machine import State

logger = logging.getLogger("apps.payments")


@transaction.atomic
def simulate_payment(
    *,
    policy: Policy,
    method: str,
    idempotency_key: str | None = None,
    actor=None,
    source: str = "api",
) -> Payment:
    if method not in Payment.Method.values:
        raise ValidationError({"method": "Unsupported payment method."})

    policy = Policy.objects.select_for_update().get(pk=policy.pk)
    amount = policy.premium
    currency = policy.currency

    # Idempotency is checked BEFORE state, so a genuine retry of a request that
    # already bound the policy replays cleanly instead of hitting "not accepted".
    if idempotency_key:
        existing = Payment.objects.filter(idempotency_key=idempotency_key).first()
        if existing is not None:
            same_request = (
                existing.policy_id == policy.pk
                and existing.method == method
                and existing.amount == amount
            )
            if same_request:
                return existing
            raise DuplicateRequest()

    if policy.state != State.ACCEPTED:
        raise PaymentNotAllowed()

    succeeded = method == Payment.Method.CARD
    payment = Payment.objects.create(
        policy=policy,
        amount=amount,
        currency=currency,
        method=method,
        status=Payment.Status.SUCCEEDED if succeeded else Payment.Status.PENDING,
        idempotency_key=idempotency_key or None,
        provider_payload={"simulated": True, "method": method},
        settled_at=timezone.now() if succeeded else None,
    )

    logger.info(
        "payment.recorded",
        extra={
            "extra_fields": {
                "payment_reference": str(payment.reference),
                "policy_id": policy.pk,
                "method": method,
                "status": payment.status,
                "amount": str(amount),
                "currency": currency,
            }
        },
    )

    activate_policy(
        policy=policy,
        actor=actor,
        source=source,
        metadata={
            "payment_reference": str(payment.reference),
            "method": method,
            "payment_status": payment.status,
        },
    )
    return payment
