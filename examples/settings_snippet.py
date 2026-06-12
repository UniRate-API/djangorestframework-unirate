"""Example wiring for djangorestframework-unirate.

Drop these fragments into a real Django project. The UniRate API key is read
from settings (or the ``UNIRATE_API_KEY`` environment variable) and never
leaves your server — API clients only ever talk to *your* endpoints.
"""

# ---------------------------------------------------------------------------
# settings.py
# ---------------------------------------------------------------------------
INSTALLED_APPS = [
    # ... your apps ...
    "rest_framework",
    "rest_framework_unirate",
]

# Required: your UniRate API key (get one free at https://unirateapi.com).
UNIRATE_API_KEY = "your-api-key"

# Optional tuning:
UNIRATE_TIMEOUT = 30  # seconds (default 30)
UNIRATE_CACHE_TIMEOUT = 300  # cache latest rates in Django's cache for 5 min
UNIRATE_DEFAULT_BASE_CURRENCY = "USD"  # used when a request omits `from`

# Optional: handle UniRate errors consistently across *all* DRF views.
# (The bundled views already do this themselves, so this is only needed if
# you call the accessor from your own views.)
REST_FRAMEWORK = {
    "EXCEPTION_HANDLER": "rest_framework_unirate.exceptions.unirate_exception_handler",
}


# ---------------------------------------------------------------------------
# urls.py — mount the ready-made rate/convert/currency endpoints
# ---------------------------------------------------------------------------
from django.urls import include, path  # noqa: E402

urlpatterns = [
    path("api/fx/", include("rest_framework_unirate.urls")),
    # exposes:
    #   GET /api/fx/rates/?from=USD&to=EUR
    #   GET /api/fx/rates/?from=USD            (all pairs)
    #   GET /api/fx/convert/?from=USD&to=EUR&amount=100
    #   GET /api/fx/currencies/
]


# ---------------------------------------------------------------------------
# Using the accessor + fields directly in your own serializers
# ---------------------------------------------------------------------------
from rest_framework import serializers  # noqa: E402

from rest_framework_unirate.client import get_accessor  # noqa: E402
from rest_framework_unirate.fields import ConvertedAmountField  # noqa: E402


class ProductSerializer(serializers.Serializer):
    name = serializers.CharField()
    price = serializers.FloatField()
    currency = serializers.CharField()
    # Add a live-converted EUR price computed from the row's own currency.
    price_eur = ConvertedAmountField(
        amount_field="price",
        from_currency_field="currency",
        to_currency="EUR",
    )


def latest_usd_eur() -> float:
    return get_accessor().get_rate("USD", "EUR")
