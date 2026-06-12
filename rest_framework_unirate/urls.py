"""URL patterns for the UniRate DRF endpoints.

Wire them under any prefix::

    from django.urls import include, path

    urlpatterns = [
        path("api/fx/", include("rest_framework_unirate.urls")),
    ]

which exposes ``api/fx/rates/``, ``api/fx/convert/``, and
``api/fx/currencies/``.
"""

from __future__ import annotations

from django.urls import path

from rest_framework_unirate import views

app_name = "unirate"

urlpatterns = [
    path("rates/", views.ExchangeRateView.as_view(), name="rates"),
    path("convert/", views.ConvertView.as_view(), name="convert"),
    path("currencies/", views.SupportedCurrenciesView.as_view(), name="currencies"),
]
