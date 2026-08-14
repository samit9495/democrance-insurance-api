"""Auth endpoints (REQUIREMENTS 8.3): JWT obtain/refresh/verify, logout, me.

Obtain/refresh/verify are open (they *are* the way in); logout and me require a
valid principal. Logout blacklists the refresh token, so with rotation on it
genuinely revokes the session.
"""

from __future__ import annotations

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)

from apps.accounts.serializers import MeSerializer


class LoginView(TokenObtainPairView):
    """``POST /auth/token/`` -> {access, refresh}, throttled against stuffing."""

    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "auth"


class RefreshView(TokenRefreshView):
    permission_classes = [AllowAny]


class VerifyView(TokenVerifyView):
    permission_classes = [AllowAny]


@extend_schema(request=OpenApiTypes.OBJECT, responses=OpenApiTypes.OBJECT)
class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        raw = request.data.get("refresh") if isinstance(request.data, dict) else None
        if not raw:
            raise ValidationError({"refresh": "This field is required."})
        try:
            RefreshToken(raw).blacklist()
        except TokenError as exc:
            raise ValidationError({"refresh": "Invalid or expired refresh token."}) from exc
        return Response({"detail": "Logged out."}, status=status.HTTP_200_OK)


@extend_schema(responses=MeSerializer)
class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(MeSerializer(request.user).data)
