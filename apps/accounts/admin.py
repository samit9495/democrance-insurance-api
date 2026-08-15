"""Admin for the custom email-login User (REQUIREMENTS 6.1, ADR-0008).

Uses Django's ``BaseUserAdmin`` so password management is handled properly: the
add form hashes ``password1``/``password2``, the change form shows the password
as a read-only hash, and a dedicated set-password view lives at
``admin:accounts_user_password_change``. The stock forms are re-pointed from
``username`` to this model's ``email`` login field.
"""

from __future__ import annotations

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import UserChangeForm, UserCreationForm

from apps.accounts.models import User


class AdminUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ("email", "role")


class AdminUserChangeForm(UserChangeForm):
    class Meta:
        model = User
        fields = "__all__"


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    add_form = AdminUserCreationForm
    form = AdminUserChangeForm

    ordering = ("email",)
    list_display = ("email", "role", "is_staff", "is_active", "date_joined")
    list_filter = ("role", "is_staff", "is_superuser", "is_active")
    search_fields = ("email", "first_name", "last_name")
    readonly_fields = ("last_login", "date_joined")

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Profile", {"fields": ("first_name", "last_name", "role")}),
        (
            "Permissions",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "role", "password1", "password2"),
            },
        ),
    )
