"""Request- and response-shaping serializers for the UniRate API views.

The query serializers validate inbound query parameters; the response
serializers exist mainly to give the browsable API and any schema generator
(drf-spectacular etc.) an accurate picture of each endpoint's output.
"""

from __future__ import annotations

from rest_framework import serializers

from rest_framework_unirate.client import get_default_base_currency
from rest_framework_unirate.fields import CurrencyCodeField


class RateQuerySerializer(serializers.Serializer):
    """Query params for the latest-rates endpoint.

    The public query keys are ``from`` and ``to``; map them onto these field
    names with :func:`rest_framework_unirate.views.map_query_params` before
    validating.
    """

    from_currency = CurrencyCodeField(required=False)
    to_currency = CurrencyCodeField(required=False)

    def to_internal_value(self, data: object) -> dict:
        result = super().to_internal_value(data)
        result.setdefault("from_currency", get_default_base_currency())
        return result


class ConvertQuerySerializer(serializers.Serializer):
    """Query params for the conversion endpoint."""

    from_currency = CurrencyCodeField(required=False)
    to_currency = CurrencyCodeField(required=True)
    amount = serializers.FloatField(required=False, default=1.0)

    def to_internal_value(self, data: object) -> dict:
        result = super().to_internal_value(data)
        result.setdefault("from_currency", get_default_base_currency())
        return result


class RateResponseSerializer(serializers.Serializer):
    from_currency = serializers.CharField()
    to_currency = serializers.CharField()
    rate = serializers.FloatField()


class RatesResponseSerializer(serializers.Serializer):
    base = serializers.CharField()
    rates = serializers.DictField(child=serializers.FloatField())


class ConvertResponseSerializer(serializers.Serializer):
    from_currency = serializers.CharField()
    to_currency = serializers.CharField()
    amount = serializers.FloatField()
    result = serializers.FloatField()


class CurrenciesResponseSerializer(serializers.Serializer):
    currencies = serializers.ListField(child=serializers.CharField())


__all__ = [
    "ConvertQuerySerializer",
    "ConvertResponseSerializer",
    "CurrenciesResponseSerializer",
    "RateQuerySerializer",
    "RateResponseSerializer",
    "RatesResponseSerializer",
]
