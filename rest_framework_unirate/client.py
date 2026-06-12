"""Django-aware wrapper around the official ``unirate-api`` Python client.

Reads configuration from Django settings, lazily instantiates one
:class:`unirate.UnirateClient` per process, and routes latest-rate /
conversion / supported-currency lookups through Django's cache framework
when ``UNIRATE_CACHE_TIMEOUT`` is set.

The wrapper is intentionally thin: it does **not** reimplement HTTP. All
network access still goes through the official client, so behaviour and
error mapping stay aligned with every other UniRate client library. The DRF
views, fields, and exception handler in this package all funnel through
this accessor.
"""

from __future__ import annotations

import os
from collections.abc import Callable
from typing import TYPE_CHECKING, Any, TypeVar, cast

from django.conf import settings
from django.core.cache import cache as default_cache
from django.core.cache import caches

if TYPE_CHECKING:
    from unirate import UnirateClient

T = TypeVar("T")


SETTING_API_KEY = "UNIRATE_API_KEY"
SETTING_TIMEOUT = "UNIRATE_TIMEOUT"
SETTING_BASE_URL = "UNIRATE_BASE_URL"
SETTING_CACHE_TIMEOUT = "UNIRATE_CACHE_TIMEOUT"
SETTING_CACHE_ALIAS = "UNIRATE_CACHE_ALIAS"
SETTING_DEFAULT_BASE = "UNIRATE_DEFAULT_BASE_CURRENCY"

DEFAULT_BASE_CURRENCY = "USD"


def get_default_base_currency() -> str:
    """The base currency used when a request omits ``from``."""
    return str(getattr(settings, SETTING_DEFAULT_BASE, DEFAULT_BASE_CURRENCY)).upper()


class UniRateAccessor:
    """Cached, Django-settings-driven UniRate client wrapper.

    The accessor is normally consumed through :func:`get_accessor` so that
    the same instance is reused for the lifetime of the process. Pass an
    explicit ``client`` only in tests where the underlying
    :class:`unirate.UnirateClient` is being substituted.
    """

    def __init__(self, *, client: UnirateClient | None = None) -> None:
        self._explicit_client = client
        self._client: UnirateClient | None = client

    # ------------------------------------------------------------------
    # Underlying client
    # ------------------------------------------------------------------

    @property
    def client(self) -> UnirateClient:
        if self._client is not None:
            return self._client
        self._client = self._build_client()
        return self._client

    @staticmethod
    def _build_client() -> UnirateClient:
        from unirate import UnirateClient

        api_key = getattr(settings, SETTING_API_KEY, None) or os.environ.get(
            SETTING_API_KEY
        )
        if not api_key:
            msg = (
                "UniRate API key not configured. Set settings.UNIRATE_API_KEY "
                "or the UNIRATE_API_KEY environment variable."
            )
            raise RuntimeError(msg)
        kwargs: dict[str, Any] = {"api_key": api_key}
        timeout = getattr(settings, SETTING_TIMEOUT, None)
        if timeout is not None:
            kwargs["timeout"] = timeout
        client = UnirateClient(**kwargs)
        base_url = getattr(settings, SETTING_BASE_URL, None)
        if base_url:
            client.BASE_URL = base_url.rstrip("/")
        return client

    # ------------------------------------------------------------------
    # Public lookup helpers (with optional Django-cache wrapping)
    # ------------------------------------------------------------------

    def get_rate(self, from_currency: str, to_currency: str) -> float:
        """Latest exchange rate for the ``from -> to`` pair."""
        base = from_currency.upper()
        quote = to_currency.upper()
        if base == quote:
            return 1.0
        cache_key = f"unirate:rate:{base}:{quote}"

        def _fetch() -> float:
            return float(self.client.get_rate(from_currency=base, to_currency=quote))

        return self._cached(cache_key, _fetch)

    def get_rates(self, from_currency: str) -> dict[str, float]:
        """Latest exchange rates for ``from`` against every supported currency."""
        base = from_currency.upper()
        cache_key = f"unirate:rates:{base}"

        def _fetch() -> dict[str, float]:
            rates = self.client.get_rate(from_currency=base)
            return {code: float(value) for code, value in dict(rates).items()}

        return self._cached(cache_key, _fetch)

    def convert(self, from_currency: str, to_currency: str, amount: float) -> float:
        """Convert ``amount`` between two currencies at the latest rate."""
        base = from_currency.upper()
        quote = to_currency.upper()
        if base == quote:
            return float(amount)
        return float(amount) * self.get_rate(base, quote)

    def get_supported_currencies(self) -> list[str]:
        """Return the list of supported currency codes."""
        cache_key = "unirate:currencies"

        def _fetch() -> list[str]:
            return list(self.client.get_supported_currencies())

        return self._cached(cache_key, _fetch)

    def get_historical_rate(
        self, from_currency: str, to_currency: str, date: str
    ) -> float:
        """Historical rate on ``date`` (``YYYY-MM-DD``). Pro-gated."""
        return float(
            self.client.get_historical_rate(
                from_currency=from_currency.upper(),
                to_currency=to_currency.upper(),
                date=date,
            )
        )

    def convert_historical(
        self,
        from_currency: str,
        to_currency: str,
        amount: float,
        date: str,
    ) -> float:
        """Convert ``amount`` at the rate observed on ``date``. Pro-gated."""
        return float(
            self.client.convert_historical(
                from_currency=from_currency.upper(),
                to_currency=to_currency.upper(),
                amount=amount,
                date=date,
            )
        )

    # ------------------------------------------------------------------
    # Cache plumbing
    # ------------------------------------------------------------------

    def _cached(self, key: str, fetch: Callable[[], T]) -> T:
        timeout = getattr(settings, SETTING_CACHE_TIMEOUT, None)
        if not timeout:
            return fetch()
        cache = self._resolve_cache()
        try:
            cached_value = cache.get(key)
        except Exception:
            cached_value = None
        if cached_value is not None:
            return cast(T, cached_value)
        value = fetch()
        try:
            cache.set(key, value, timeout=timeout)
        except Exception:
            pass
        return value

    @staticmethod
    def _resolve_cache() -> Any:
        alias = getattr(settings, SETTING_CACHE_ALIAS, None)
        if alias:
            return caches[alias]
        return default_cache


_ACCESSOR: UniRateAccessor | None = None


def get_accessor() -> UniRateAccessor:
    """Return the process-wide :class:`UniRateAccessor` instance."""
    global _ACCESSOR
    if _ACCESSOR is None:
        _ACCESSOR = UniRateAccessor()
    return _ACCESSOR


def _reset_accessor() -> None:
    """Drop the cached accessor. Used by tests; not part of the public API."""
    global _ACCESSOR
    _ACCESSOR = None


__all__ = [
    "UniRateAccessor",
    "get_accessor",
    "get_default_base_currency",
]
