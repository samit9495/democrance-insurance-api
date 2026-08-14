"""One uniform error envelope for every failure (REQUIREMENTS 8.5).

    {"error": {"code": "...", "message": "...", "details": {...}}}

Domain exceptions can carry an explicit ``error_code``; everything else is
mapped from the HTTP status code.
"""

from __future__ import annotations

from typing import Any

from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import status
from rest_framework.exceptions import APIException
from rest_framework.serializers import as_serializer_error
from rest_framework.views import exception_handler as drf_exception_handler

from apps.common.errors import STATUS_TO_CODE, ErrorCode


class DomainError(APIException):
    """Base for domain rule violations that map to a specific envelope code."""

    status_code = status.HTTP_409_CONFLICT
    error_code = ErrorCode.INVALID_STATE_TRANSITION
    default_detail = "The request could not be completed."

    def __init__(self, detail: str | None = None, details: dict[str, Any] | None = None):
        super().__init__(detail)
        self.extra_details = details or {}


def _code_for(exc: Exception, status_code: int) -> str:
    explicit = getattr(exc, "error_code", None)
    if explicit:
        return explicit
    return STATUS_TO_CODE.get(status_code, "error")


def _message_and_details(exc: Exception, data: Any) -> tuple[str, Any]:
    extra = getattr(exc, "extra_details", None)
    if isinstance(data, dict) and set(data) == {"detail"}:
        return str(data["detail"]), (extra or {})
    if isinstance(data, dict):
        return "Validation failed.", data
    if isinstance(data, list):
        message = "; ".join(str(item) for item in data) or "Request failed."
        return message, (extra or {})
    return str(data), (extra or {})


def custom_exception_handler(exc: Exception, context: dict[str, Any]):
    if isinstance(exc, DjangoValidationError):
        from rest_framework.exceptions import ValidationError as DRFValidationError

        exc = DRFValidationError(detail=as_serializer_error(exc))

    response = drf_exception_handler(exc, context)
    if response is None:
        return None

    code = _code_for(exc, response.status_code)
    message, details = _message_and_details(exc, response.data)
    response.data = {"error": {"code": code, "message": message, "details": details}}
    return response
