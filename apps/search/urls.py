"""Unified search route under /api/v1/ (both slash spellings)."""

from django.urls import path

from apps.search.views import SearchView

search = SearchView.as_view()

urlpatterns = [
    path("search/", search, name="search"),
    path("search", search),
]
