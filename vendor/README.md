# Vendored p99 C sources

This directory contains a pinned snapshot of the
[p99](https://github.com/synesissoftware/p99) C library, compiled into the
`p99._ext` extension at build time.

Current snapshot: **0.1.1** (`P99_VER_ALPHABETA = 0x41`).

Files:

- `include/p99/p99.h` — public C API;
- `src/histogram.c` — implementation;
- `src/p99_portable.h` — internal helpers (not installed upstream);
- `CMakeLists.txt` — minimal static-library target for the Python build;

Update this snapshot when bumping the Python package version to match a new
p99 C release.
