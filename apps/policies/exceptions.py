"""Policy domain exceptions."""

from rest_framework import status

from apps.common.errors import ErrorCode
from apps.common.exceptions import DomainError


class InvalidStateTransition(DomainError):
    """A requested policy state change is not permitted by the state machine."""

    status_code = status.HTTP_409_CONFLICT
    error_code = ErrorCode.INVALID_STATE_TRANSITION
    default_detail = "That policy state transition is not allowed."


class QuoteExpired(InvalidStateTransition):
    """The quote's validity window has passed; it can no longer be accepted."""

    default_detail = "This quote has expired and can no longer be accepted."
