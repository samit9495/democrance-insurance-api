"""Quote routes under /api/v1/.

The RPC-style ``/quote/`` dispatcher and the REST ``/quotes/...`` aliases are
each exposed in trailing-slash and slashless form, so a reviewer can copy either
spelling straight off the sequence diagram (APPEND_SLASH cannot rescue a
slashless POST — it would discard the body).
"""

from django.urls import path

from apps.policies.views import (
    PolicyDetailView,
    PolicyHistoryView,
    PolicyListView,
    QuoteAcceptView,
    QuoteCollectionView,
    QuoteDispatchView,
    QuotePayView,
)

dispatch = QuoteDispatchView.as_view()
collection = QuoteCollectionView.as_view()
accept = QuoteAcceptView.as_view()
pay = QuotePayView.as_view()
policy_list = PolicyListView.as_view()
policy_detail = PolicyDetailView.as_view()
policy_history = PolicyHistoryView.as_view()

urlpatterns = [
    path("quote/", dispatch, name="quote"),
    path("quote", dispatch),
    path("quotes/", collection, name="quotes"),
    path("quotes", collection),
    path("quotes/<int:pk>/accept/", accept, name="quote-accept"),
    path("quotes/<int:pk>/accept", accept),
    path("quotes/<int:pk>/pay/", pay, name="quote-pay"),
    path("quotes/<int:pk>/pay", pay),
    path("policies/", policy_list, name="policy-list"),
    path("policies", policy_list),
    path("policies/<int:pk>/history/", policy_history, name="policy-history"),
    path("policies/<int:pk>/history", policy_history),
    path("policies/<int:pk>/", policy_detail, name="policy-detail"),
    path("policies/<int:pk>", policy_detail),
]
