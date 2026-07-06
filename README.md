# p99.Python

![Python](https://img.shields.io/badge/Python-3776AB?style=flat&logo=python&logoColor=white)
[![License](https://img.shields.io/badge/License-BSD_3--Clause-blue.svg)](https://opensource.org/licenses/BSD-3-Clause)

Python bindings for [**p99**](https://github.com/synesissoftware/p99): a
low-cost, fixed-size histogram for recording event durations and querying
high-resolution percentiles (p50, p90, p99, and beyond).

This package provides:

- a **C extension** that embeds the vendored p99 C library for maximum
  performance; and
- a **pure-Python fallback** with identical semantics when the extension is
  unavailable.

## Installation

```bash
pip install p99
```

On supported platforms, `pip` installs a pre-built wheel with the C extension.
Otherwise the pure-Python implementation is used automatically.

Force the pure-Python backend (for debugging or CI):

```bash
P99_PURE_PYTHON=1 python -c "import p99; print(p99.__implementation__)"
```

## Quick start

```python
import p99

h = p99.Histogram()
h.push_ns(150)
h.push_us(5)
h.push_ms(10)

print(h.event_count)        # 3
print(h.value_at_p99())     # approximated duration in nanoseconds
print(p99.__implementation__)  # "c" or "python"
```

## Development

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest
P99_PURE_PYTHON=1 pytest
```

Build requirements for the C extension: a C11 compiler and CMake 3.16+.

## Vendored C library

The p99 C sources are vendored under `vendor/p99/` and compiled into the
`_ext` module at build time. End users do not need a system install of
libp99.

## License

BSD 3-Clause License. See [LICENSE](LICENSE).
