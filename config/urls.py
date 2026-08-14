"""Root URL configuration.

Grows phase by phase: /admin/ lands in the scaffold; /healthz/, the /api/v1/
surface, docs and the demo SPA are wired in as their phases deliver them.
"""

from django.contrib import admin
from django.urls import path

urlpatterns = [
    path("admin/", admin.site.urls),
]
