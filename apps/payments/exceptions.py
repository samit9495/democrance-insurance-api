"""Payment domain exceptions (uniform envelope, REQUIREMENTS 8.5)."""

from rest_framework import status

from apps.common.errors import ErrorCode
from apps.common.exceptions import DomainError


class PaymentNotAllowed(DomainError):
    """A payment was attempted against a policy that is not an accepted quote."""

    status_code = status.HTTP_409_CONFLICT
    error_code = ErrorCode.INVALID_STATE_TRANSITION
    default_detail = "Payment is only allowed on an accepted quote."


class DuplicateRequest(DomainError):
    """An Idempotency-Key was reused for a materially different request."""

    status_code = status.HTTP_409_CONFLICT
    error_code = ErrorCode.DUPLICATE_REQUEST
    default_detail = "A different request with this Idempotency-Key has already been processed."
