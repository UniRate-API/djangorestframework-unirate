"""Drop-in DRF API views that proxy UniRate.

Mount them via :mod:`rest_framework_unirate.urls` (``include``) or wire each
view individually. The UniRate API key never leaves the server: clients call
*your* endpoints, and the views fetch from UniRate using the key configured
in Django settings.

Each view installs :func:`unirate_exception_handler` so ``unirate`` errors
map to sensible HTTP responses even when the project has not set it globally.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from rest_framework_unirate.client import get_accessor
from rest_framework_unirate.exceptions import unirate_exception_handler
from rest_framework_unirate.serializers import (
    ConvertQuerySerializer,
    RateQuerySerializer,
)

# Public query keys -> internal serializer field names. ``from`` is a Python
# keyword, so it cannot be a serializer field name directly.
_QUERY_PARAM_MAP = {
    "from": "from_currency",
    "to": "to_currency",
    "amount": "amount",
}


def map_query_params(query_params: Any) -> dict[str, Any]:
    """Translate inbound ``from``/``to``/``amount`` keys to field names."""
    return {
        field: query_params[key]
        for key, field in _QUERY_PARAM_MAP.items()
        if key in query_params
    }


class UniRateBaseView(APIView):
    """Shared base wiring the UniRate-aware exception handler."""

    def get_exception_handler(self) -> Callable[[Exception, Any], Any]:
        return unirate_exception_handler


class ExchangeRateView(UniRateBaseView):
    """``GET`` latest exchange rate(s).

    * ``?from=USD&to=EUR`` → ``{"from_currency", "to_currency", "rate"}``
    * ``?from=USD``        → ``{"base", "rates": {...}}`` (all pairs)
    """

    def get(self, request: Request) -> Response:
        query = RateQuerySerializer(data=map_query_params(request.query_params))
        query.is_valid(raise_exception=True)
        data = query.validated_data
        base = data["from_currency"]
        accessor = get_accessor()
        to_currency = data.get("to_currency")
        if to_currency:
            rate = accessor.get_rate(base, to_currency)
            return Response(
                {
                    "from_currency": base,
                    "to_currency": to_currency,
                    "rate": rate,
                }
            )
        return Response({"base": base, "rates": accessor.get_rates(base)})


class ConvertView(UniRateBaseView):
    """``GET ?from=USD&to=EUR&amount=100`` → converted ``result``."""

    def get(self, request: Request) -> Response:
        query = ConvertQuerySerializer(data=map_query_params(request.query_params))
        query.is_valid(raise_exception=True)
        data = query.validated_data
        base = data["from_currency"]
        to_currency = data["to_currency"]
        amount = data["amount"]
        result = get_accessor().convert(base, to_currency, amount)
        return Response(
            {
                "from_currency": base,
                "to_currency": to_currency,
                "amount": amount,
                "result": result,
            }
        )


class SupportedCurrenciesView(UniRateBaseView):
    """``GET`` the list of supported currency codes."""

    def get(self, request: Request) -> Response:
        return Response({"currencies": get_accessor().get_supported_currencies()})


__all__ = [
    "ConvertView",
    "ExchangeRateView",
    "SupportedCurrenciesView",
    "UniRateBaseView",
]
