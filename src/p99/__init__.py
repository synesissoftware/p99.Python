"""p99 — low-cost performance percentile histogram for Python."""

from __future__ import annotations

import os

__version__ = "0.1.1"
__all__ = [
    'Histogram',
    '__implementation__',
    '__version__',
]


def _load() -> tuple[type, str]:
    if os.environ.get("P99_PURE_PYTHON"):
        from ._pure import Histogram

        return Histogram, "python"
    try:
        from ._ext import Histogram

        return Histogram, "c"
    except ImportError:
        from ._pure import Histogram

        return Histogram, "python"


Histogram, __implementation__ = _load()
