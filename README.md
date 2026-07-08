# djangorestframework-unirate

Django REST Framework integration for the [UniRate](https://unirateapi.com)
currency-exchange API. Drop-in API views for live exchange rates, conversion,
and supported-currency lookups — plus serializer fields and a cached,
settings-driven client — all keeping your UniRate API key safely server-side.

- **Drop-in endpoints** — mount three ready-made views (`rates`, `convert`,
  `currencies`) under any URL prefix; clients call *your* API, never UniRate
  directly, so the key never reaches the browser.
- **Serializer fields** — `CurrencyCodeField` (normalises/validates ISO-4217
  codes) and `ConvertedAmountField` (live-converts a model's amount into a
  target currency).
- **Thin & aligned** — wraps the official [`unirate-api`](https://pypi.org/project/unirate-api/)
  Python client, so behaviour and error semantics match every other UniRate
  library. Optional Django-cache integration. Zero extra runtime deps.

Companion to [`UniRateBackend` in django-money](https://github.com/django-money/django-money):
django-money gives you a UniRate *exchange backend*; this package gives you a
UniRate-powered *REST surface* on top of DRF.

## Install

```bash
pip install djangorestframework-unirate
```

Add it to `INSTALLED_APPS` and configure your key:

```python
INSTALLED_APPS = [
    # ...
    "rest_framework",
    "rest_framework_unirate",
]

UNIRATE_API_KEY = "your-api-key"  # or set the UNIRATE_API_KEY env var
```

Get a free API key at [unirateapi.com](https://unirateapi.com).

## Quick start — drop-in endpoints

```python
# urls.py
from django.urls import include, path

urlpatterns = [
    path("api/fx/", include("rest_framework_unirate.urls")),
]
```

That exposes:

| Endpoint | Example | Response |
|---|---|---|
| `GET api/fx/rates/?from=USD&to=EUR` | single pair | `{"from_currency": "USD", "to_currency": "EUR", "rate": 0.92}` |
| `GET api/fx/rates/?from=USD` | all pairs | `{"base": "USD", "rates": {"EUR": 0.92, "GBP": 0.79, ...}}` |
| `GET api/fx/convert/?from=USD&to=EUR&amount=100` | convert | `{"from_currency": "USD", "to_currency": "EUR", "amount": 100.0, "result": 92.0}` |
| `GET api/fx/currencies/` | supported list | `{"currencies": ["USD", "EUR", "GBP", ...]}` |

`from` defaults to `UNIRATE_DEFAULT_BASE_CURRENCY` (USD); `amount` defaults to
`1`. Currency codes are case-insensitive and normalised to upper-case.

## Serializer fields

### `ConvertedAmountField`

Adds a live-converted amount to any serializer, derived from a sibling
currency field:

```python
from rest_framework import serializers
from rest_framework_unirate.fields import ConvertedAmountField

class ProductSerializer(serializers.Serializer):
    name = serializers.CharField()
    price = serializers.FloatField()
    currency = serializers.CharField()
    price_eur = ConvertedAmountField(
        amount_field="price",
        from_currency_field="currency",   # or from_currency="USD"
        to_currency="EUR",                # or omit + pass context={"target_currency": ...}
    )
```

### `CurrencyCodeField`

A `CharField` that upper-cases input and enforces a 3-letter alphabetic code.
Pass `validate_supported=True` to additionally check it against the live
`/api/currencies` list (one cached call):

```python
from rest_framework_unirate.fields import CurrencyCodeField

class QuoteSerializer(serializers.Serializer):
    base = CurrencyCodeField()
    quote = CurrencyCodeField(validate_supported=True)
```

## Using the client directly

```python
from rest_framework_unirate.client import get_accessor

accessor = get_accessor()
accessor.get_rate("USD", "EUR")          # 0.92
accessor.get_rates("USD")                # {"EUR": 0.92, "GBP": 0.79, ...}
accessor.convert("USD", "EUR", 100)      # 92.0
accessor.get_supported_currencies()      # ["USD", "EUR", ...]
```

## Configuration

| Setting | Default | Purpose |
|---|---|---|
| `UNIRATE_API_KEY` | — (required) | Your UniRate API key |
| `UNIRATE_TIMEOUT` | `30` | HTTP timeout in seconds |
| `UNIRATE_BASE_URL` | `https://api.unirateapi.com` | Override the API base URL |
| `UNIRATE_CACHE_TIMEOUT` | `None` | Seconds to cache rates/currencies in Django's cache (off when unset) |
| `UNIRATE_CACHE_ALIAS` | `default` | Which `CACHES` alias to use |
| `UNIRATE_DEFAULT_BASE_CURRENCY` | `USD` | Base currency when a request omits `from` |

## Error handling

The bundled views map `unirate` client errors onto sensible HTTP responses:

| Situation | Status |
|---|---|
| Unknown currency (upstream 404) | `404 Not Found` |
| Bad parameters (upstream 400) | `400 Bad Request` |
| Upstream rate limit (429) | `429 Too Many Requests` |
| Bad server-side API key / Pro-gated 403 | `502 Bad Gateway` |
| UniRate unavailable (503) / network failure | `503` / `502` |

Because the API key is server-side, an upstream `401` is treated as a gateway
misconfiguration (`502`), not as a client auth failure. To apply the same
mapping to your *own* DRF views, set the handler globally:

```python
REST_FRAMEWORK = {
    "EXCEPTION_HANDLER": "rest_framework_unirate.exceptions.unirate_exception_handler",
}
```

## Rate limits

Latest rates, conversion, and the currency list are free-tier endpoints.
Historical rates and time-series are Pro-gated and return `403` on the free
tier. Set `UNIRATE_CACHE_TIMEOUT` to cut your upstream call volume.

## Compatibility

- Python 3.10–3.13
- Django 4.2, 5.0, 5.1, 5.2
- Django REST Framework 3.15–3.16

<!-- unirate-ecosystem-footer:start -->
## UniRate ecosystem

UniRate ships official integrations for 40+ ecosystems, all maintained under the
[UniRate-API](https://github.com/UniRate-API) org.

**Core clients (9 languages)**
[Python](https://github.com/UniRate-API/unirate-api-python) ·
[Node.js / TypeScript](https://github.com/UniRate-API/unirate-api-nodejs) ·
[Go](https://github.com/UniRate-API/unirate-api-go) ·
[Rust](https://github.com/UniRate-API/unirate-api-rust) ·
[Java](https://github.com/UniRate-API/unirate-api-java) ·
[Ruby](https://github.com/UniRate-API/unirate-api-ruby) ·
[PHP](https://github.com/UniRate-API/unirate-api-php) ·
[.NET](https://github.com/UniRate-API/unirate-api-dotnet) ·
[Swift](https://github.com/UniRate-API/unirate-api-swift)

**JavaScript / TypeScript**
[React](https://github.com/UniRate-API/react-unirate) ·
[Next.js](https://github.com/UniRate-API/next-unirate) ·
[Remix](https://github.com/UniRate-API/remix-unirate) ·
[SvelteKit](https://github.com/UniRate-API/sveltekit-unirate) ·
[Vue](https://github.com/UniRate-API/vue-unirate) ·
[Angular](https://github.com/UniRate-API/angular-unirate) ·
[Nuxt](https://github.com/UniRate-API/nuxt-unirate) ·
[NestJS](https://github.com/UniRate-API/nestjs-unirate) ·
[tRPC](https://github.com/UniRate-API/trpc-unirate)

**Static-site generators**
[Astro](https://github.com/UniRate-API/astro-unirate) ·
[Eleventy](https://github.com/UniRate-API/eleventy-unirate) ·
[Hugo](https://github.com/UniRate-API/hugo-unirate) ·
[Jekyll](https://github.com/UniRate-API/jekyll-unirate)

**CMS & e-commerce**
[Wagtail](https://github.com/UniRate-API/wagtail-unirate) ·
[WordPress](https://github.com/UniRate-API/unirate-currency-converter) ·
[WooCommerce](https://github.com/UniRate-API/unirate-woocs) ·
[Drupal](https://github.com/UniRate-API/drupal-unirate) ·
[Strapi](https://github.com/UniRate-API/strapi-plugin-unirate) ·
[Medusa](https://github.com/UniRate-API/medusa-plugin-unirate) ·
[Symfony](https://github.com/UniRate-API/unirate-bundle) ·
[Laravel](https://github.com/UniRate-API/laravel-money-unirate) ·
[Directus](https://github.com/UniRate-API/directus-extension-unirate)

**Data, AI & backend**
[LangChain (Python)](https://github.com/UniRate-API/langchain-unirate) ·
[LangChain.js](https://github.com/UniRate-API/langchain-js-unirate) ·
[FastAPI](https://github.com/UniRate-API/fastapi-unirate) ·
[Flask](https://github.com/UniRate-API/flask-unirate) ·
[Django REST Framework](https://github.com/UniRate-API/djangorestframework-unirate) ·
[Apache Airflow](https://github.com/UniRate-API/airflow-provider-unirate) ·
[dbt](https://github.com/UniRate-API/dbt-unirate)

**Platform & tools**
[MCP server](https://github.com/UniRate-API/unirate-mcp) ·
[CLI](https://github.com/UniRate-API/unirate-cli) ·
[Cloudflare Workers](https://github.com/UniRate-API/cloudflare-workers-unirate) ·
[Home Assistant](https://github.com/UniRate-API/unirate-home-assistant) ·
[n8n](https://github.com/UniRate-API/n8n-nodes-unirate) ·
[Google Sheets](https://github.com/UniRate-API/unirate-sheets) ·
[VS Code](https://github.com/UniRate-API/vscode-unirate) ·
[Obsidian](https://github.com/UniRate-API/obsidian-currency)

**Money library bridges**
[money gem (Ruby)](https://github.com/UniRate-API/money-unirate-api) ·
[NodaMoney (.NET)](https://github.com/UniRate-API/UniRateApi.NodaMoney)

Get a free API key at [unirateapi.com](https://unirateapi.com).
<!-- unirate-ecosystem-footer:end -->

## License

MIT — see [LICENSE](LICENSE).