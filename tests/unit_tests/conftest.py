"""Shared pytest fixtures.

The HTTP layer is mocked with ``responses`` so we exercise the real
``unirate-api`` client + the DRF wiring around it. Each test gets a clean
cache + a fresh process-wide accessor so cached values from a previous test
do not bleed in.
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

import pytest
import responses

from rest_framework_unirate import client as client_module

UNIRATE_BASE = "https://api.unirateapi.com"


@pytest.fixture
def mocked_responses() -> Iterator[responses.RequestsMock]:
    with responses.RequestsMock(assert_all_requests_are_fired=False) as mock:
        yield mock


@pytest.fixture(autouse=True)
def _reset_accessor() -> Iterator[None]:
    client_module._reset_accessor()
    yield
    client_module._reset_accessor()


@pytest.fixture(autouse=True)
def _clear_cache() -> Iterator[None]:
    from django.core.cache import cache

    cache.clear()
    yield
    cache.clear()


@pytest.fixture
def api_client() -> Any:
    from rest_framework.test import APIClient

    return APIClient()


@pytest.fixture
def override_settings_factory(settings: Any) -> Any:
    """Convenience wrapper for setting/un-setting UniRate settings keys."""

    def _apply(**kwargs: Any) -> None:
        for key, value in kwargs.items():
            setattr(settings, key, value)

    return _apply
