"""Root URL configuration.

Grows phase by phase: /admin/ lands in the scaffold; /healthz/, the /api/v1/
surface, docs and the demo SPA are wired in as their phases deliver them.
"""

from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

from apps.common.views import healthz

admin.site.site_header = "Democrance Insurance"
admin.site.site_title = "Democrance Admin"
admin.site.index_title = "Operations"

urlpatterns = [
    path("admin/", admin.site.urls),
    path("healthz/", healthz, name="healthz"),
    path("api/v1/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "api/v1/docs/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="swagger-ui",
    ),
    path("api/v1/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
    path("api/v1/", include("apps.accounts.urls")),
    path("api/v1/", include("apps.customers.urls")),
    path("api/v1/", include("apps.policies.urls")),
    path("api/v1/", include("apps.search.urls")),
    path("", include("apps.web.urls")),
]
