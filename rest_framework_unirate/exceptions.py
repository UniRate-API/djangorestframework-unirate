"""Map ``unirate`` client errors onto Django REST Framework responses.

UniRate API key handling lives entirely server-side, so an upstream ``401``
means *your server's* key is wrong — that is a gateway/config problem, not a
client-auth problem, and is surfaced as ``502 Bad Gateway`` rather than
leaking a misleading ``401`` to the caller. Genuine caller-input faults
(unknown currency, bad date) keep their natural ``404`` / ``400`` codes, and
upstream rate-limiting is propagated as ``429`` so clients back off.

The views in this package wire :func:`unirate_exception_handler` in
automatically, so it works out-of-the-box regardless of a project's global
``REST_FRAMEWORK['EXCEPTION_HANDLER']`` setting. Projects that want UniRate
errors handled everywhere can also set it as their global handler.
"""

from __future__ import annotations

from typing import Any

from rest_framework import status
from rest_framework.exceptions import APIException
from rest_framework.views import exception_handler as drf_exception_handler
from unirate.exceptions import (
    APIError,
    AuthenticationError,
    InvalidCurrencyError,
    InvalidDateError,
    RateLimitError,
    UnirateError,
)


class UniRateUpstreamError(APIException):
    """The UniRate API returned an error we cannot attribute to the caller."""

    status_code = status.HTTP_502_BAD_GATEWAY
    default_detail = "The currency-rate provider returned an error."
    default_code = "unirate_upstream_error"


class UniRateUnavailable(APIException):
    """The UniRate API (or the network path to it) is unavailable."""

    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    default_detail = "The currency-rate provider is temporarily unavailable."
    default_code = "unirate_unavailable"


class UniRateInvalidRequest(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Invalid currency-conversion request parameters."
    default_code = "unirate_invalid_request"


class UniRateCurrencyNotFound(APIException):
    status_code = status.HTTP_404_NOT_FOUND
    default_detail = "Currency not found or no data available."
    default_code = "unirate_currency_not_found"


class UniRateRateLimited(APIException):
    status_code = status.HTTP_429_TOO_MANY_REQUESTS
    default_detail = "Upstream currency-rate provider rate limit exceeded."
    default_code = "unirate_rate_limited"


def translate_unirate_error(exc: UnirateError) -> APIException:
    """Convert a ``unirate`` exception into the matching DRF ``APIException``."""
    if isinstance(exc, InvalidDateError):
        return UniRateInvalidRequest(detail=str(exc) or None)
    if isinstance(exc, InvalidCurrencyError):
        return UniRateCurrencyNotFound(detail=str(exc) or None)
    if isinstance(exc, RateLimitError):
        return UniRateRateLimited(detail=str(exc) or None)
    if isinstance(exc, AuthenticationError):
        # Server-side key problem — a gateway error, not a client 401.
        return UniRateUpstreamError(
            detail="The currency-rate provider rejected the configured API key."
        )
    if isinstance(exc, APIError):
        if exc.status_code == status.HTTP_503_SERVICE_UNAVAILABLE:
            return UniRateUnavailable(detail=str(exc) or None)
        return UniRateUpstreamError(detail=str(exc) or None)
    # Base UnirateError covers wrapped network failures and Pro-gated 403s.
    return UniRateUpstreamError(detail=str(exc) or None)


def unirate_exception_handler(exc: Exception, context: Any) -> Any:
    """DRF exception handler that understands ``unirate`` errors.

    Non-UniRate exceptions fall through to DRF's default handler unchanged.
    """
    if isinstance(exc, UnirateError):
        exc = translate_unirate_error(exc)
    return drf_exception_handler(exc, context)


__all__ = [
    "UniRateCurrencyNotFound",
    "UniRateInvalidRequest",
    "UniRateRateLimited",
    "UniRateUnavailable",
    "UniRateUpstreamError",
    "translate_unirate_error",
    "unirate_exception_handler",
]
