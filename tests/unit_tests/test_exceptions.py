"""Tests for the UniRate -> DRF exception mapping."""

from __future__ import annotations

import pytest
from unirate.exceptions import (
    APIError,
    AuthenticationError,
    InvalidCurrencyError,
    InvalidDateError,
    RateLimitError,
    UnirateError,
)

from rest_framework_unirate.exceptions import (
    translate_unirate_error,
    unirate_exception_handler,
)


@pytest.mark.parametrize(
    ("exc", "expected_status"),
    [
        (InvalidDateError("bad date"), 400),
        (InvalidCurrencyError("no such currency"), 404),
        (RateLimitError("slow down"), 429),
        (AuthenticationError("bad key"), 502),
        (APIError("unavailable", 503), 503),
        (APIError("teapot", 418), 502),
        (UnirateError("network blew up"), 502),
    ],
)
def test_translate_status_codes(exc: UnirateError, expected_status: int) -> None:
    assert translate_unirate_error(exc).status_code == expected_status


def test_handler_translates_unirate_error() -> None:
    response = unirate_exception_handler(RateLimitError("slow down"), {"view": None})
    assert response is not None
    assert response.status_code == 429


def test_handler_passes_through_non_unirate_errors() -> None:
    from rest_framework.exceptions import NotAuthenticated

    response = unirate_exception_handler(NotAuthenticated(), {"view": None})
    assert response is not None
    assert response.status_code == 401


def test_handler_returns_none_for_unknown_exception() -> None:
    # DRF's default handler returns None for exceptions it does not know,
    # so the framework can re-raise / 500.
    assert unirate_exception_handler(ValueError("boom"), {"view": None}) is None
