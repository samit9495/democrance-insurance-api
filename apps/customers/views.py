"""Customer HTTP views (thin — validation and persistence live in the serializer)."""

from rest_framework import generics

from apps.customers.models import Customer
from apps.customers.serializers import CustomerSerializer


class CreateCustomerView(generics.CreateAPIView):
    """Create a customer (diagram step 1, REQ-P1-2/4).

    Backs both the RPC-style ``/create_customer/`` and the REST ``/customers/``
    routes (ENH-01, ADR-0001).
    """

    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer
