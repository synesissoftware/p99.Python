"""Tests for the p99 Python histogram."""

from __future__ import annotations

import importlib

import pytest

from p99._pure import BUCKET_COUNT, UINT64_MAX, Histogram as PureHistogram


def test_version() -> None:
    import p99

    assert p99.__version__ == "0.1.1"


def test_default_histogram(histogram) -> None:
    assert histogram.event_count == 0
    assert histogram.event_time_total() == 0
    assert histogram.event_time_total_raw() == 0
    assert histogram.has_overflowed is False
    assert histogram.min_ns() is None
    assert histogram.max_ns() is None

    for i in range(BUCKET_COUNT):
        assert histogram.buckets_view()[i] == 0
        assert histogram.bucket_value(i) == 0

    assert histogram.bucket_value(64) is None


def test_bucket_placement(histogram) -> None:
    cases = [
        (0, 0),
        (1, 0),
        (2, 1),
        (3, 1),
        (4, 2),
        (7, 2),
        (8, 3),
        (15, 3),
        (1024, 10),
        (2047, 10),
        (1 << 63, 63),
        (UINT64_MAX, 63),
    ]

    for value, bucket in cases:
        histogram.clear()
        assert histogram.push_ns(value)
        assert histogram.bucket_value(bucket) == 1

    assert histogram.bucket_value(64) is None


def test_push_events(histogram) -> None:
    assert histogram.push_ns(1)
    assert histogram.push_ns(3)
    assert histogram.push_us(10)
    assert histogram.push_ms(5)
    assert histogram.push_s(2)
    assert histogram.push_ns(100)

    assert histogram.event_count == 6
    assert histogram.has_overflowed is False
    assert histogram.min_ns() == 1
    assert histogram.max_ns() == 2_000_000_000
    assert histogram.event_time_total() == 2_005_010_104

    buckets = histogram.buckets_view()
    assert buckets[0] == 1
    assert buckets[1] == 1
    assert buckets[6] == 1
    assert buckets[13] == 1
    assert buckets[22] == 1
    assert buckets[30] == 1

    histogram.clear()
    assert histogram.event_count == 0
    assert histogram.event_time_total() == 0


def test_overflow(histogram) -> None:
    assert histogram.push_ns(UINT64_MAX)
    assert histogram.event_time_total() == UINT64_MAX
    assert histogram.has_overflowed is False

    assert histogram.push_ns(1) is False
    assert histogram.has_overflowed is True
    assert histogram.event_time_total() is None
    assert histogram.event_time_total_raw() == UINT64_MAX


def test_percentiles_empty(histogram) -> None:
    assert histogram.value_at_percentile(50.0) is None
    assert histogram.value_at_p50() is None
    assert histogram.value_at_p99() is None
    assert histogram.fixed_percentiles() is None
    assert histogram.values_at_percentiles([50.0]) is None


def test_percentiles_single_event(histogram) -> None:
    assert histogram.push_ns(100)

    for percentile in (0.0, 50.0, 99.0, 100.0):
        assert histogram.value_at_percentile(percentile) == 100

    assert histogram.value_at_p50() == 100
    assert histogram.value_at_p90() == 100
    assert histogram.value_at_p99() == 100
    assert histogram.value_at_p99_999_9() == 100


def test_percentiles_interpolation(histogram) -> None:
    assert histogram.push_ns(100)
    assert histogram.push_ns(200)

    p50 = histogram.value_at_p50()
    p99 = histogram.value_at_p99()
    assert p50 is not None and p99 is not None
    assert 100 <= p50 <= 200
    assert 100 <= p99 <= 200
    assert histogram.value_at_percentile(0.0) == 100
    assert histogram.value_at_percentile(100.0) == 200


def test_percentiles_wide_range(histogram) -> None:
    values = [
        1,
        10,
        100,
        1_000,
        10_000,
        100_000,
        1_000_000,
        10_000_000,
        100_000_000,
        1_000_000_000,
        10_000_000_000,
    ]

    for value in values:
        assert histogram.push_ns(value)

    assert histogram.event_count == len(values)
    assert histogram.min_ns() == 1
    assert histogram.max_ns() == 10_000_000_000

    fixed = histogram.fixed_percentiles()
    assert fixed is not None
    ordered = [
        fixed['p50'],
        fixed['p75'],
        fixed['p90'],
        fixed['p95'],
        fixed['p99'],
        fixed['p99.5'],
        fixed['p99.9'],
        fixed['p99.99'],
        fixed['p99.999'],
        fixed['p99.9999'],
    ]
    assert ordered == sorted(ordered)
    assert ordered[0] >= 1
    assert ordered[-1] <= 10_000_000_000


def test_percentiles_many_events(histogram) -> None:
    count = 100_000
    for i in range(1, count + 1):
        assert histogram.push_ns(i)

    assert histogram.event_count == count
    assert histogram.min_ns() == 1
    assert histogram.max_ns() == count
    assert histogram.value_at_p50() == 50_000
    assert histogram.value_at_p90() == 100_000
    assert histogram.value_at_p99() == 100_000
    assert histogram.value_at_p99_9() == 100_000


def test_compare_float_and_int_percentiles(histogram) -> None:
    for i in range(1, 10_001):
        assert histogram.push_ns((i * i) % 1_000_000)

    pairs = [
        (50.0, histogram.value_at_p50),
        (75.0, histogram.value_at_p75),
        (90.0, histogram.value_at_p90),
        (95.0, histogram.value_at_p95),
        (99.0, histogram.value_at_p99),
        (99.5, histogram.value_at_p99_5),
        (99.9, histogram.value_at_p99_9),
        (99.99, histogram.value_at_p99_99),
        (99.999, histogram.value_at_p99_999),
        (99.9999, histogram.value_at_p99_999_9),
    ]

    for level, named_fn in pairs:
        float_value = histogram.value_at_percentile(level)
        int_value = named_fn()
        assert float_value is not None and int_value is not None
        tolerance = max(abs(float_value) * 0.01, 1.0)
        assert abs(float_value - int_value) <= tolerance


def test_values_at_percentiles_empty_levels(histogram) -> None:
    assert histogram.push_ns(100)
    assert histogram.values_at_percentiles([]) == []


def test_backends_match() -> None:
    pytest.importorskip("p99._ext")

    import p99

    if p99.__implementation__ != "c":
        pytest.skip("C extension not active")

    from p99._ext import Histogram as CHistogram
    from p99._pure import Histogram as PyHistogram

    sequences = [
        [1, 3, 10_000, 5_000_000, 100],
        [(i * i) % 1_000_000 for i in range(1, 5_001)],
        list(range(1, 10_001)),
    ]

    for seq in sequences:
        c_hist = CHistogram()
        py_hist = PyHistogram()
        for value in seq:
            assert c_hist.push_ns(value) == py_hist.push_ns(value)

        assert c_hist.event_count == py_hist.event_count
        assert c_hist.has_overflowed == py_hist.has_overflowed
        assert c_hist.event_time_total_raw() == py_hist.event_time_total_raw()
        assert c_hist.buckets_view() == py_hist.buckets_view()
        assert c_hist.min_ns() == py_hist.min_ns()
        assert c_hist.max_ns() == py_hist.max_ns()

        for method in (
            'value_at_p50',
            'value_at_p75',
            'value_at_p90',
            'value_at_p95',
            'value_at_p99',
            'value_at_p99_5',
            'value_at_p99_9',
            'value_at_p99_99',
            'value_at_p99_999',
            'value_at_p99_999_9',
        ):
            assert getattr(c_hist, method)() == getattr(py_hist, method)()

        levels = [0.0, 50.0, 75.0, 90.0, 99.0, 99.9, 100.0]
        assert c_hist.values_at_percentiles(levels) == py_hist.values_at_percentiles(
            levels
        )
        assert c_hist.fixed_percentiles() == py_hist.fixed_percentiles()

    overflow_c = CHistogram()
    overflow_py = PureHistogram()
    assert overflow_c.push_ns(UINT64_MAX) == overflow_py.push_ns(UINT64_MAX)
    assert overflow_c.push_ns(1) == overflow_py.push_ns(1)
    assert overflow_c.has_overflowed == overflow_py.has_overflowed

    importlib.reload(p99)
