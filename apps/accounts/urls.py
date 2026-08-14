"""Auth routes under /api/v1/auth/ (REQUIREMENTS 8.3)."""

from django.urls import path

from apps.accounts.views import LoginView, LogoutView, MeView, RefreshView, VerifyView

urlpatterns = [
    path("auth/token/", LoginView.as_view(), name="token-obtain"),
    path("auth/token/refresh/", RefreshView.as_view(), name="token-refresh"),
    path("auth/token/verify/", VerifyView.as_view(), name="token-verify"),
    path("auth/logout/", LogoutView.as_view(), name="logout"),
    path("auth/me/", MeView.as_view(), name="me"),
]
