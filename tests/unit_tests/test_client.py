"""Tests for the :class:`UniRateAccessor` wrapper."""

from __future__ import annotations

import pytest
import responses

from rest_framework_unirate.client import (
    UniRateAccessor,
    get_accessor,
    get_default_base_currency,
)

BASE = "https://api.unirateapi.com"


def test_get_rate_round_trip(mocked_responses: responses.RequestsMock) -> None:
    mocked_responses.get(f"{BASE}/api/rates", json={"rate": "0.92"})
    assert get_accessor().get_rate("USD", "EUR") == pytest.approx(0.92)


def test_get_rate_same_currency_skips_http(
    mocked_responses: responses.RequestsMock,
) -> None:
    assert get_accessor().get_rate("USD", "usd") == 1.0
    assert len(mocked_responses.calls) == 0


def test_get_rates_all_pairs(mocked_responses: responses.RequestsMock) -> None:
    mocked_responses.get(
        f"{BASE}/api/rates",
        json={"rates": {"EUR": "0.92", "GBP": "0.79"}},
    )
    rates = get_accessor().get_rates("USD")
    assert rates == {"EUR": pytest.approx(0.92), "GBP": pytest.approx(0.79)}


def test_convert_round_trip(mocked_responses: responses.RequestsMock) -> None:
    mocked_responses.get(f"{BASE}/api/rates", json={"rate": "0.92"})
    assert get_accessor().convert("USD", "EUR", 100) == pytest.approx(92.0)


def test_convert_same_currency_returns_amount(
    mocked_responses: responses.RequestsMock,
) -> None:
    assert get_accessor().convert("GBP", "GBP", 50) == 50.0
    assert len(mocked_responses.calls) == 0


def test_get_supported_currencies(
    mocked_responses: responses.RequestsMock,
) -> None:
    mocked_responses.get(
        f"{BASE}/api/currencies", json={"currencies": ["USD", "EUR", "GBP"]}
    )
    assert get_accessor().get_supported_currencies() == ["USD", "EUR", "GBP"]


def test_missing_api_key_raises(settings) -> None:  # type: ignore[no-untyped-def]
    settings.UNIRATE_API_KEY = ""
    accessor = UniRateAccessor()
    with pytest.raises(RuntimeError, match="UniRate API key not configured"):
        _ = accessor.client


def test_default_base_currency_default() -> None:
    assert get_default_base_currency() == "USD"


def test_default_base_currency_override(settings) -> None:  # type: ignore[no-untyped-def]
    settings.UNIRATE_DEFAULT_BASE_CURRENCY = "gbp"
    assert get_default_base_currency() == "GBP"


def test_cache_respected_when_timeout_set(
    mocked_responses: responses.RequestsMock,
    override_settings_factory,  # type: ignore[no-untyped-def]
) -> None:
    override_settings_factory(UNIRATE_CACHE_TIMEOUT=60)
    mocked_responses.get(f"{BASE}/api/rates", json={"rate": "0.92"})
    a = UniRateAccessor()
    assert a.get_rate("USD", "EUR") == pytest.approx(0.92)
    # Second call hits the cache; only one HTTP call should have been made.
    assert a.get_rate("USD", "EUR") == pytest.approx(0.92)
    assert len(mocked_responses.calls) == 1


def test_cache_skipped_when_timeout_unset(
    mocked_responses: responses.RequestsMock,
) -> None:
    mocked_responses.get(f"{BASE}/api/rates", json={"rate": "0.92"})
    mocked_responses.get(f"{BASE}/api/rates", json={"rate": "0.93"})
    a = UniRateAccessor()
    assert a.get_rate("USD", "EUR") == pytest.approx(0.92)
    assert a.get_rate("USD", "EUR") == pytest.approx(0.93)
    assert len(mocked_responses.calls) == 2


def test_base_url_override(
    mocked_responses: responses.RequestsMock,
    settings,  # type: ignore[no-untyped-def]
) -> None:
    settings.UNIRATE_BASE_URL = "https://example.test"
    mocked_responses.get("https://example.test/api/rates", json={"rate": "1.1"})
    assert get_accessor().get_rate("EUR", "USD") == pytest.approx(1.1)
