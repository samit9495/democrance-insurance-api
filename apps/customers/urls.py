"""Customer routes under /api/v1/.

Both the RPC-style path and the REST alias are exposed, each in trailing-slash
and slashless form so a reviewer can copy either spelling off the sequence
diagram verbatim (APPEND_SLASH cannot rescue a slashless POST).
"""

from django.urls import path

from apps.customers.views import CreateCustomerView, CustomerListCreateView

create_customer = CreateCustomerView.as_view()
customers = CustomerListCreateView.as_view()

urlpatterns = [
    path("create_customer/", create_customer, name="create-customer"),
    path("create_customer", create_customer),
    path("customers/", customers, name="customers"),
    path("customers", customers),
]
