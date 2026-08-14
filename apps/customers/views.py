"""Customer HTTP views (thin — validation and persistence live in the serializer).

Creation is staff/agent-only (customers cannot create customers); the list is
scoped so a customer principal sees only its own record — 404, not 403, for
anyone else's (REQUIREMENTS 9.1/9.2).
"""

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, generics

from apps.accounts.permissions import DemoOrAuthenticated, DemoOrStaff, scope_customers
from apps.customers.filters import CustomerFilterSet
from apps.customers.models import Customer
from apps.customers.serializers import CustomerSerializer


class CreateCustomerView(generics.CreateAPIView):
    """Create a customer via the RPC-style ``/create_customer/`` (diagram step 1)."""

    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer
    permission_classes = [DemoOrStaff]


class CustomerListCreateView(generics.ListCreateAPIView):
    """REST ``/customers/``: POST creates (staff only), GET lists/searches (scoped)."""

    serializer_class = CustomerSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_class = CustomerFilterSet
    ordering_fields = ["last_name", "first_name", "created_at"]
    ordering = ["last_name", "first_name", "id"]

    def get_permissions(self):
        if self.request.method == "POST":
            return [DemoOrStaff()]
        return [DemoOrAuthenticated()]

    def get_queryset(self):
        return scope_customers(Customer.objects.all(), self.request.user)
