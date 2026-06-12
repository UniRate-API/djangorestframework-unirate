"""Minimal Django + DRF settings for the test suite."""

from __future__ import annotations

SECRET_KEY = "test-secret-key"

DEBUG = True

USE_TZ = True

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.auth",
    "rest_framework",
    "rest_framework_unirate",
]

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "drf-unirate-tests",
    },
}

ROOT_URLCONF = "tests.unit_tests.urls"

REST_FRAMEWORK: dict = {}

UNIRATE_API_KEY = "test-key"
