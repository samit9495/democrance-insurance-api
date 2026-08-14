"""Quote and policy lifecycle services (thin-view/fat-service, domain-invariants).

The ONLY place `Policy.state` is mutated. Every mutation runs inside
`transaction.atomic()` with `select_for_update()` on the policy row and writes a
`PolicyStateTransition` in the same transaction, so history can never drift from
state and two concurrent binds cannot both win.
"""

from __future__ import annotations

import datetime
import logging
from decimal import Decimal

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from apps.policies.exceptions import QuoteExpired
from apps.policies.models import Policy, PolicyStateTransition
from apps.policies.state_machine import State, assert_can_transition
from apps.products.models import ProductType
from apps.products.rating import calculate_premium, select_rule

logger = logging.getLogger("apps.policies")


def _apply_transition(
    policy: Policy,
    to_state: str,
    *,
    actor=None,
    source: str = "api",
    reason: str = "",
    metadata: dict | None = None,
) -> None:
    """Validate then record a transition, mutating ``policy.state`` in memory.

    Raises before writing anything if the move is illegal, so a rejected
    transition never leaves an audit row behind.
    """
    from_state = policy.state
    assert_can_transition(from_state, to_state)
    policy.state = to_state
    PolicyStateTransition.objects.create(
        policy=policy,
        from_state=from_state,
        to_state=to_state,
        actor=actor,
        source=source,
        reason=reason,
        metadata=metadata or {},
    )
    logger.info(
        "policy.transition",
        extra={
            "extra_fields": {
                "policy_id": policy.pk,
                "from_state": from_state,
                "to_state": to_state,
                "source": source,
                "actor_id": getattr(actor, "pk", None),
            }
        },
    )


@transaction.atomic
def create_quote(
    *,
    customer,
    product: ProductType,
    cover: Decimal | None = None,
    actor=None,
    source: str = "api",
    as_of: datetime.date | None = None,
) -> Policy:
    as_of = as_of or timezone.localdate()
    cover = product.default_cover if cover is None else cover
    age = customer.age_at(as_of)

    premium = calculate_premium(product, age, cover, as_of)
    rule = select_rule(product, age, as_of)
    now = timezone.now()

    policy = Policy.objects.create(
        customer=customer,
        product=product,
        cover=cover,
        currency=product.currency,
        premium=premium,
        rating_rule=rule,
        rated_age=age,
        rated_at=now,
        created_by=actor,
        state=State.NEW,
    )
    # Genesis transition: the policy enters the machine at ``new``.
    PolicyStateTransition.objects.create(
        policy=policy,
        from_state=None,
        to_state=State.NEW,
        actor=actor,
        source=source,
        reason="quote created",
        metadata={"premium": str(premium)},
    )
    _apply_transition(
        policy,
        State.QUOTED,
        actor=actor,
        source=source,
        reason="quote priced",
        metadata={"premium": str(premium)},
    )
    policy.quoted_at = now
    policy.quote_expires_at = now + datetime.timedelta(days=settings.QUOTE_VALIDITY_DAYS)
    policy.save(update_fields=["state", "quoted_at", "quote_expires_at", "updated_at"])
    return policy


@transaction.atomic
def accept_quote(*, policy: Policy, actor=None, source: str = "api") -> Policy:
    policy = Policy.objects.select_for_update().get(pk=policy.pk)
    if policy.is_expired:
        raise QuoteExpired()

    _apply_transition(policy, State.ACCEPTED, actor=actor, source=source, reason="quote accepted")
    policy.accepted_at = timezone.now()
    policy.save(update_fields=["state", "accepted_at", "updated_at"])
    return policy


@transaction.atomic
def activate_policy(
    *, policy: Policy, actor=None, source: str = "api", metadata: dict | None = None
) -> Policy:
    policy = Policy.objects.select_for_update().get(pk=policy.pk)

    _apply_transition(
        policy,
        State.ACTIVE,
        actor=actor,
        source=source,
        reason="policy activated",
        metadata=metadata or {},
    )
    policy.activated_at = timezone.now()
    policy.save(update_fields=["state", "activated_at", "updated_at"])
    return policy
