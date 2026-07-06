"""Shared fixtures for p99.Python tests."""

from __future__ import annotations

import importlib
import os
from typing import Iterator

import pytest


def _reload_p99(*, pure_python: bool) -> object:
    if pure_python:
        os.environ["P99_PURE_PYTHON"] = "1"
    else:
        os.environ.pop("P99_PURE_PYTHON", None)

    import p99

    return importlib.reload(p99)


@pytest.fixture(params=["c", "python"])
def p99_module(request: pytest.FixtureRequest) -> Iterator[object]:
    if request.param == "c":
        module = _reload_p99(pure_python=False)
        if module.__implementation__ != "c":
            pytest.skip("C extension not available")
    else:
        module = _reload_p99(pure_python=True)

    yield module

    os.environ.pop("P99_PURE_PYTHON", None)
    importlib.reload(importlib.import_module("p99"))


@pytest.fixture
def histogram(p99_module: object):
    return p99_module.Histogram()
