"""Customer HTTP views (thin — validation and persistence live in the serializer)."""

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, generics

from apps.customers.filters import CustomerFilterSet
from apps.customers.models import Customer
from apps.customers.serializers import CustomerSerializer


class CreateCustomerView(generics.CreateAPIView):
    """Create a customer via the RPC-style ``/create_customer/`` (diagram step 1)."""

    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer


class CustomerListCreateView(generics.ListCreateAPIView):
    """REST ``/customers/``: POST creates (ADR-0001), GET lists/searches (Part 3)."""

    serializer_class = CustomerSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_class = CustomerFilterSet
    ordering_fields = ["last_name", "first_name", "created_at"]
    ordering = ["last_name", "first_name", "id"]

    def get_queryset(self):
        return Customer.objects.all()
