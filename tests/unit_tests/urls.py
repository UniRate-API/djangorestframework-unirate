"""Root URLconf for the test suite — mounts the package views under /fx/."""

from __future__ import annotations

from django.urls import include, path

urlpatterns = [
    path("fx/", include("rest_framework_unirate.urls")),
]
