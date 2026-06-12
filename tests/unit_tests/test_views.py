"""Tests for the drop-in API views (exercised through DRF's APIClient)."""

from __future__ import annotations

from typing import Any

import responses

BASE = "https://api.unirateapi.com"


def test_rates_view_single_pair(
    api_client: Any, mocked_responses: responses.RequestsMock
) -> None:
    mocked_responses.get(f"{BASE}/api/rates", json={"rate": "0.92"})
    resp = api_client.get("/fx/rates/", {"from": "USD", "to": "EUR"})
    assert resp.status_code == 200
    assert resp.json() == {
        "from_currency": "USD",
        "to_currency": "EUR",
        "rate": 0.92,
    }


def test_rates_view_all_pairs(
    api_client: Any, mocked_responses: responses.RequestsMock
) -> None:
    mocked_responses.get(
        f"{BASE}/api/rates", json={"rates": {"EUR": "0.92", "GBP": "0.79"}}
    )
    resp = api_client.get("/fx/rates/", {"from": "USD"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["base"] == "USD"
    assert body["rates"] == {"EUR": 0.92, "GBP": 0.79}


def test_rates_view_defaults_to_usd(
    api_client: Any, mocked_responses: responses.RequestsMock
) -> None:
    mocked_responses.get(f"{BASE}/api/rates", json={"rates": {"EUR": "0.92"}})
    resp = api_client.get("/fx/rates/")
    assert resp.status_code == 200
    assert resp.json()["base"] == "USD"


def test_rates_view_lowercase_query_is_normalised(
    api_client: Any, mocked_responses: responses.RequestsMock
) -> None:
    mocked_responses.get(f"{BASE}/api/rates", json={"rate": "0.92"})
    resp = api_client.get("/fx/rates/", {"from": "usd", "to": "eur"})
    assert resp.status_code == 200
    assert resp.json()["to_currency"] == "EUR"


def test_convert_view(
    api_client: Any, mocked_responses: responses.RequestsMock
) -> None:
    mocked_responses.get(f"{BASE}/api/rates", json={"rate": "0.92"})
    resp = api_client.get("/fx/convert/", {"from": "USD", "to": "EUR", "amount": "100"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["result"] == 92.0
    assert body["amount"] == 100.0
    assert body["from_currency"] == "USD"
    assert body["to_currency"] == "EUR"


def test_convert_view_defaults_amount_to_one(
    api_client: Any, mocked_responses: responses.RequestsMock
) -> None:
    mocked_responses.get(f"{BASE}/api/rates", json={"rate": "0.92"})
    resp = api_client.get("/fx/convert/", {"to": "EUR"})
    assert resp.status_code == 200
    assert resp.json()["amount"] == 1.0


def test_convert_view_requires_to(api_client: Any) -> None:
    resp = api_client.get("/fx/convert/", {"from": "USD"})
    assert resp.status_code == 400
    assert "to_currency" in resp.json()


def test_currencies_view(
    api_client: Any, mocked_responses: responses.RequestsMock
) -> None:
    mocked_responses.get(
        f"{BASE}/api/currencies", json={"currencies": ["USD", "EUR", "GBP"]}
    )
    resp = api_client.get("/fx/currencies/")
    assert resp.status_code == 200
    assert resp.json() == {"currencies": ["USD", "EUR", "GBP"]}


def test_rates_view_unknown_currency_maps_to_404(
    api_client: Any, mocked_responses: responses.RequestsMock
) -> None:
    mocked_responses.get(f"{BASE}/api/rates", status=404, json={})
    resp = api_client.get("/fx/rates/", {"from": "USD", "to": "ZZZ"})
    assert resp.status_code == 404


def test_convert_view_rate_limit_maps_to_429(
    api_client: Any, mocked_responses: responses.RequestsMock
) -> None:
    mocked_responses.get(f"{BASE}/api/rates", status=429, json={})
    resp = api_client.get("/fx/convert/", {"from": "USD", "to": "EUR"})
    assert resp.status_code == 429


def test_rates_view_pro_gated_maps_to_502(
    api_client: Any, mocked_responses: responses.RequestsMock
) -> None:
    # A 403 (Pro-gated / bad server key path) surfaces as a gateway error.
    mocked_responses.get(f"{BASE}/api/rates", status=403, json={})
    resp = api_client.get("/fx/rates/", {"from": "USD", "to": "EUR"})
    assert resp.status_code == 502
