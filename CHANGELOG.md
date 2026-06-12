# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project
adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] — 2026-06-12

### Added

- `UniRateAccessor` — a cached, Django-settings-driven wrapper around the
  official `unirate-api` Python client, with optional Django-cache
  integration (`UNIRATE_CACHE_TIMEOUT`).
- Drop-in DRF API views (`ExchangeRateView`, `ConvertView`,
  `SupportedCurrenciesView`) mountable via `rest_framework_unirate.urls`,
  keeping the UniRate API key server-side.
- Serializer fields: `CurrencyCodeField` (normalises + optionally validates
  ISO-4217 codes) and `ConvertedAmountField` (live currency conversion on a
  model's monetary amount).
- `unirate_exception_handler` — maps `unirate` client errors onto sensible
  HTTP responses (404 / 400 / 429 for caller-input faults; 502 / 503 for
  upstream/gateway problems).
- `responses`-backed mock test suite + CI matrix across Python 3.10–3.13,
  Django 4.2–5.2, and DRF 3.15–3.16.
