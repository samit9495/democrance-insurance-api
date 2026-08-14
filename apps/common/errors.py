"""Canonical error codes and their HTTP status mapping (REQUIREMENTS 8.5)."""


class ErrorCode:
    VALIDATION = "validation_error"
    AUTHENTICATION_FAILED = "authentication_failed"
    PERMISSION_DENIED = "permission_denied"
    NOT_FOUND = "not_found"
    METHOD_NOT_ALLOWED = "method_not_allowed"
    INVALID_STATE_TRANSITION = "invalid_state_transition"
    DUPLICATE_REQUEST = "duplicate_request"
    THROTTLED = "throttled"
    SERVER_ERROR = "server_error"


# Fallback mapping used when an exception does not declare its own code.
STATUS_TO_CODE = {
    400: ErrorCode.VALIDATION,
    401: ErrorCode.AUTHENTICATION_FAILED,
    403: ErrorCode.PERMISSION_DENIED,
    404: ErrorCode.NOT_FOUND,
    405: ErrorCode.METHOD_NOT_ALLOWED,
    409: ErrorCode.INVALID_STATE_TRANSITION,
    429: ErrorCode.THROTTLED,
    500: ErrorCode.SERVER_ERROR,
}
