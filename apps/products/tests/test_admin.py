"""Phase 3: products admin is editable and surfaces overlap as a form error."""

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

from apps.products.models import RatingRule
from apps.products.tests.factories import ProductTypeFactory, RatingRuleFactory


@pytest.fixture
def admin_client_(client):
    admin = get_user_model().objects.create_superuser(email="admin@example.com", password="pw")
    client.force_login(admin)
    return client


@pytest.mark.django_db
@pytest.mark.parametrize("model", ["producttype", "ratingrule"])
def test_products_changelists_render(admin_client_, model):
    url = reverse(f"admin:products_{model}_changelist")

    assert admin_client_.get(url).status_code == 200


@pytest.mark.django_db
def test_admin_rejects_an_overlapping_rating_band(admin_client_):
    product = ProductTypeFactory()
    RatingRuleFactory(product=product, age_band_min=18, age_band_max=30)

    add_url = reverse("admin:products_ratingrule_add")
    response = admin_client_.post(
        add_url,
        {
            "product": str(product.pk),
            "age_band_min": "25",
            "age_band_max": "40",
            "rate_per_1000_cover": "1.0000",
            "loading_factor": "1.0000",
            "min_premium": "50.00",
            "valid_from": "2020-01-01",
            "valid_to": "",
            "is_active": "on",
            "_save": "Save",
        },
    )

    assert response.status_code == 200  # form redisplayed with the error
    assert RatingRule.objects.filter(product=product).count() == 1
