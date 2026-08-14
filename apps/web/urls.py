"""Demo SPA route at the site root."""

from django.urls import path

from apps.web.views import DemoView

urlpatterns = [
    path("", DemoView.as_view(), name="demo"),
]
