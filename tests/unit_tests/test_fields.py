"""Tests for the serializer fields."""

from __future__ import annotations

import pytest
import responses
from rest_framework import serializers

from rest_framework_unirate.fields import ConvertedAmountField, CurrencyCodeField

BASE = "https://api.unirateapi.com"


class _CodeSerializer(serializers.Serializer):
    code = CurrencyCodeField()


class _ValidatedCodeSerializer(serializers.Serializer):
    code = CurrencyCodeField(validate_supported=True)


def test_currency_code_field_uppercases() -> None:
    s = _CodeSerializer(data={"code": "eur"})
    assert s.is_valid(), s.errors
    assert s.validated_data["code"] == "EUR"


def test_currency_code_field_rejects_bad_length() -> None:
    s = _CodeSerializer(data={"code": "EURO"})
    assert not s.is_valid()
    assert "code" in s.errors


def test_currency_code_field_rejects_non_alpha() -> None:
    s = _CodeSerializer(data={"code": "U$D"})
    assert not s.is_valid()
    assert "code" in s.errors


def test_currency_code_field_validate_supported_ok(
    mocked_responses: responses.RequestsMock,
) -> None:
    mocked_responses.get(
        f"{BASE}/api/currencies", json={"currencies": ["USD", "EUR", "GBP"]}
    )
    s = _ValidatedCodeSerializer(data={"code": "eur"})
    assert s.is_valid(), s.errors
    assert s.validated_data["code"] == "EUR"


def test_currency_code_field_validate_supported_rejects_unknown(
    mocked_responses: responses.RequestsMock,
) -> None:
    mocked_responses.get(
        f"{BASE}/api/currencies", json={"currencies": ["USD", "EUR", "GBP"]}
    )
    s = _ValidatedCodeSerializer(data={"code": "XYZ"})
    assert not s.is_valid()
    assert "not a supported currency" in str(s.errors["code"])


class _Product:
    def __init__(self, price: float, currency: str) -> None:
        self.price = price
        self.currency = currency


class _ProductSerializer(serializers.Serializer):
    price = serializers.FloatField()
    currency = serializers.CharField()
    price_eur = ConvertedAmountField(
        amount_field="price",
        from_currency_field="currency",
        to_currency="EUR",
    )


def test_converted_amount_field_from_sibling_currency(
    mocked_responses: responses.RequestsMock,
) -> None:
    mocked_responses.get(f"{BASE}/api/rates", json={"rate": "0.92"})
    data = _ProductSerializer(_Product(price=100.0, currency="USD")).data
    assert data["price_eur"] == pytest.approx(92.0)


def test_converted_amount_field_fixed_source() -> None:
    field = ConvertedAmountField(
        amount_field="price", from_currency="USD", to_currency="usd"
    )

    class _S(serializers.Serializer):
        out = field

    # USD -> USD short-circuits, no HTTP needed.
    out = _S(_Product(price=42.0, currency="USD")).data["out"]
    assert out == pytest.approx(42.0)


def test_converted_amount_field_context_target(
    mocked_responses: responses.RequestsMock,
) -> None:
    mocked_responses.get(f"{BASE}/api/rates", json={"rate": "0.79"})

    class _S(serializers.Serializer):
        gbp = ConvertedAmountField(amount_field="price", from_currency="USD")

    s = _S(_Product(price=10.0, currency="USD"), context={"target_currency": "GBP"})
    assert s.data["gbp"] == pytest.approx(7.9)


def test_converted_amount_field_requires_a_source() -> None:
    with pytest.raises(ValueError, match="from_currency"):
        ConvertedAmountField(amount_field="price", to_currency="EUR")


def test_converted_amount_field_rounding_none(
    mocked_responses: responses.RequestsMock,
) -> None:
    mocked_responses.get(f"{BASE}/api/rates", json={"rate": "0.123456"})

    class _S(serializers.Serializer):
        out = ConvertedAmountField(
            amount_field="price",
            from_currency="USD",
            to_currency="EUR",
            rounding=None,
        )

    out = _S(_Product(price=1.0, currency="USD")).data["out"]
    assert out == pytest.approx(0.123456)
