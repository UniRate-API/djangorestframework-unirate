"""Django REST Framework integration for the UniRate currency-exchange API.

The package exposes:

* :class:`rest_framework_unirate.client.UniRateAccessor` — a cached wrapper
  around the official ``unirate-api`` Python client, wired through Django
  settings, with optional Django-cache integration.
* DRF serializer fields (:mod:`rest_framework_unirate.fields`):
  :class:`~rest_framework_unirate.fields.CurrencyCodeField` and
  :class:`~rest_framework_unirate.fields.ConvertedAmountField`.
* Ready-to-mount DRF API views (:mod:`rest_framework_unirate.views`) that
  proxy ``/api/rates``, ``/api/convert``, and ``/api/currencies`` while
  keeping the UniRate API key server-side.
* A DRF exception handler (:func:`rest_framework_unirate.exceptions
  .unirate_exception_handler`) that maps ``unirate`` errors onto sensible
  HTTP responses.
"""

from __future__ import annotations

from rest_framework_unirate.client import UniRateAccessor, get_accessor

default_app_config = "rest_framework_unirate.apps.RestFrameworkUniRateConfig"

__all__ = [
    "UniRateAccessor",
    "get_accessor",
]
