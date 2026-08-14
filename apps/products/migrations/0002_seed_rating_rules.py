"""Seed the product catalogue and rating table (D6, REQUIREMENTS 6.4).

Chosen so a fresh clone can quote immediately and the brief's own example
reproduces exactly: personal-accident, age 35, cover 200000 -> premium 200.00.
"""

import datetime
from decimal import Decimal

from django.db import migrations

SEED_FROM = datetime.date(2020, 1, 1)

PRODUCTS = {
    "personal-accident": {
        "name": "Personal Accident",
        "description": "Lump-sum cover for accidental injury.",
        "default_cover": Decimal("200000.00"),
        "min_cover": Decimal("1000.00"),
        "max_cover": Decimal("1000000.00"),
        "min_age": 18,
        "max_age": 70,
        "bands": [
            (18, 25, "1.30", "50.00"),
            (26, 30, "1.15", "50.00"),
            (31, 40, "1.00", "50.00"),
            (41, 50, "1.40", "50.00"),
            (51, 60, "2.00", "50.00"),
            (61, 70, "3.10", "50.00"),
        ],
    },
    "travel": {
        "name": "Travel",
        "description": "Single-trip travel cover.",
        "default_cover": Decimal("50000.00"),
        "min_cover": Decimal("1000.00"),
        "max_cover": Decimal("500000.00"),
        "min_age": 18,
        "max_age": 65,
        "bands": [
            (18, 40, "0.60", "25.00"),
            (41, 65, "0.95", "25.00"),
        ],
    },
}


def seed(apps, schema_editor):
    ProductType = apps.get_model("products", "ProductType")
    RatingRule = apps.get_model("products", "RatingRule")

    for code, spec in PRODUCTS.items():
        product, _ = ProductType.objects.update_or_create(
            code=code,
            defaults={
                "name": spec["name"],
                "description": spec["description"],
                "is_active": True,
                "default_cover": spec["default_cover"],
                "min_cover": spec["min_cover"],
                "max_cover": spec["max_cover"],
                "min_age": spec["min_age"],
                "max_age": spec["max_age"],
            },
        )
        for lo, hi, rate, floor in spec["bands"]:
            RatingRule.objects.update_or_create(
                product=product,
                age_band_min=lo,
                age_band_max=hi,
                valid_from=SEED_FROM,
                defaults={
                    "rate_per_1000_cover": Decimal(rate),
                    "loading_factor": Decimal("1.0000"),
                    "min_premium": Decimal(floor),
                    "valid_to": None,
                    "is_active": True,
                },
            )


def unseed(apps, schema_editor):
    ProductType = apps.get_model("products", "ProductType")
    ProductType.objects.filter(code__in=PRODUCTS.keys()).delete()


class Migration(migrations.Migration):
    dependencies = [("products", "0001_initial")]

    operations = [migrations.RunPython(seed, unseed)]
