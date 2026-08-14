"""The rating engine: a pure function of (product, age, cover, as_of) + rules.

No HTTP, no request, no policy writes — just money arithmetic, so it can be
unit-tested exhaustively (domain-invariants, ADR-0006).
"""

from __future__ import annotations

import datetime
from decimal import ROUND_HALF_UP, Decimal

from rest_framework import status

from apps.common.errors import ErrorCode
from apps.common.exceptions import DomainError
from apps.products.models import ProductType, RatingRule

_CENTS = Decimal("0.01")
_PER = Decimal("1000")


class RatingError(DomainError):
    """A quote cannot be priced (missing band, ineligible product, bad cover)."""

    status_code = status.HTTP_400_BAD_REQUEST
    error_code = ErrorCode.VALIDATION
    default_detail = "The policy could not be rated."


def calculate_premium(
    product: ProductType, age: int, cover: Decimal, as_of: datetime.date
) -> Decimal:
    if not product.is_active:
        raise RatingError(f"Product '{product.code}' is not currently available.")
    if not (product.min_age <= age <= product.max_age):
        raise RatingError(f"Age {age} is outside the eligible range for '{product.code}'.")
    if not (product.min_cover <= cover <= product.max_cover):
        raise RatingError(
            f"Cover {cover} is outside the allowed range "
            f"[{product.min_cover}, {product.max_cover}] for '{product.code}'."
        )

    rule = _select_rule(product, age, as_of)
    if rule is None:
        raise RatingError(f"No active rating band for age {age} on '{product.code}'.")

    raw = (cover / _PER) * rule.rate_per_1000_cover * rule.loading_factor
    premium = raw.quantize(_CENTS, rounding=ROUND_HALF_UP)
    return max(rule.min_premium, premium)


def _select_rule(product: ProductType, age: int, as_of: datetime.date) -> RatingRule | None:
    candidates = [
        rule
        for rule in product.rating_rules.filter(is_active=True)
        if rule.covers_age(age) and rule.is_effective_on(as_of)
    ]
    if not candidates:
        return None
    # Overlap validation guarantees at most one, but be explicit: newest wins.
    return max(candidates, key=lambda rule: rule.valid_from)
