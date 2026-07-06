"""Pure-Python implementation of the p99 performance percentile histogram."""

from __future__ import annotations

import math
from typing import Sequence

BUCKET_COUNT = 64
UINT64_MAX = (1 << 64) - 1


def _llround(value: float) -> int:
    if value >= 0.0:
        return int(math.floor(value + 0.5))
    return int(math.ceil(value - 0.5))


def _u64_mul_div(multiplicand: int, multiplier: int, divisor: int) -> int:
    return (multiplicand * multiplier) // divisor


def _u64_add_mul_div(
    addend: int, multiplicand: int, multiplier: int, divisor: int
) -> int:
    return addend + _u64_mul_div(multiplicand, multiplier, divisor)


def _floor_log2_u64(value: int) -> int:
    return value.bit_length() - 1


def _bucket_index(time_in_ns: int) -> int:
    if time_in_ns <= 1:
        return 0
    return _floor_log2_u64(time_in_ns)


def _bucket_range(index: int) -> tuple[int, int] | None:
    if index >= BUCKET_COUNT:
        return None
    if index == 0:
        return 0, 1
    lower = 1 << index
    if index == BUCKET_COUNT - 1:
        upper = UINT64_MAX
    else:
        upper = (1 << (index + 1)) - 1
    return lower, upper


class Histogram:
    """Low-cost performance percentile histogram (pure-Python backend)."""

    __slots__ = (
        '_has_overflowed',
        '_event_count',
        '_event_time_total',
        '_min_event_time',
        '_max_event_time',
        '_buckets',
    )

    def __init__(self) -> None:
        self.clear()

    def clear(self) -> None:
        self._has_overflowed = False
        self._event_count = 0
        self._event_time_total = 0
        self._min_event_time = 0
        self._max_event_time = 0
        self._buckets = [0] * BUCKET_COUNT

    def push_ns(self, time_in_ns: int) -> bool:
        bucket_index = _bucket_index(time_in_ns)
        if not self._try_add_ns_to_total_and_update_minmax(time_in_ns):
            return False
        self._event_count += 1
        self._buckets[bucket_index] += 1
        return True

    def push_us(self, time_in_us: int) -> bool:
        if time_in_us > UINT64_MAX // 1000:
            self._has_overflowed = True
            return False
        return self.push_ns(time_in_us * 1000)

    def push_ms(self, time_in_ms: int) -> bool:
        if time_in_ms > UINT64_MAX // 1_000_000:
            self._has_overflowed = True
            return False
        return self.push_ns(time_in_ms * 1_000_000)

    def push_s(self, time_in_s: int) -> bool:
        if time_in_s > UINT64_MAX // 1_000_000_000:
            self._has_overflowed = True
            return False
        return self.push_ns(time_in_s * 1_000_000_000)

    @property
    def event_count(self) -> int:
        return self._event_count

    @property
    def has_overflowed(self) -> bool:
        return self._has_overflowed

    def event_time_total(self) -> int | None:
        if self._has_overflowed:
            return None
        return self.event_time_total_raw()

    def event_time_total_raw(self) -> int:
        return self._event_time_total

    def min_ns(self) -> int | None:
        if self._event_count == 0:
            return None
        return self._min_event_time

    def max_ns(self) -> int | None:
        if self._event_count == 0:
            return None
        return self._max_event_time

    def bucket_value(self, index: int) -> int | None:
        if index >= BUCKET_COUNT:
            return None
        return self._buckets[index]

    def buckets_view(self) -> tuple[int, ...]:
        return tuple(self._buckets)

    def value_at_percentile(self, percentile: float) -> int | None:
        if self._event_count == 0:
            return None

        p = _clamp_percentile(percentile)
        if p <= 0.0:
            return self.min_ns()
        if p >= 100.0:
            return self.max_ns()

        target_rank = float(self._event_count) * (p / 100.0)
        accumulated = 0

        for i in range(BUCKET_COUNT):
            count = self._buckets[i]
            if count > 0:
                prev_accumulated = accumulated
                accumulated += count
                if float(accumulated) >= target_rank:
                    return self._value_at_percentile_in_bucket(
                        i, count, prev_accumulated, target_rank
                    )

        return self.max_ns()

    def value_at_p50(self) -> int | None:
        return self._value_at_target_rank(
            _u64_mul_div(self._event_count, 1, 2)
        )

    def value_at_p75(self) -> int | None:
        return self._value_at_target_rank(
            _u64_mul_div(self._event_count, 3, 4)
        )

    def value_at_p90(self) -> int | None:
        return self._value_at_target_rank(
            _u64_mul_div(self._event_count, 90, 100)
        )

    def value_at_p95(self) -> int | None:
        return self._value_at_target_rank(
            _u64_mul_div(self._event_count, 95, 100)
        )

    def value_at_p99(self) -> int | None:
        return self._value_at_target_rank(
            _u64_mul_div(self._event_count, 99, 100)
        )

    def value_at_p99_5(self) -> int | None:
        return self._value_at_target_rank(
            _u64_mul_div(self._event_count, 995, 1000)
        )

    def value_at_p99_9(self) -> int | None:
        return self._value_at_target_rank(
            _u64_mul_div(self._event_count, 999, 1000)
        )

    def value_at_p99_99(self) -> int | None:
        return self._value_at_target_rank(
            _u64_mul_div(self._event_count, 9999, 10000)
        )

    def value_at_p99_999(self) -> int | None:
        return self._value_at_target_rank(
            _u64_mul_div(self._event_count, 99999, 100000)
        )

    def value_at_p99_999_9(self) -> int | None:
        return self._value_at_target_rank(
            _u64_mul_div(self._event_count, 999999, 1000000)
        )

    def values_at_percentiles(
        self, levels: Sequence[float]
    ) -> list[tuple[float, int]] | None:
        if self._event_count == 0:
            return None
        if not levels:
            return []

        results: list[tuple[float, int]] = []
        for level in levels:
            value = self.value_at_percentile(level)
            if value is None:
                return None
            results.append((level, value))
        return results

    def fixed_percentiles(self) -> dict[str, int] | None:
        if self._event_count == 0:
            return None

        getters = (
            ('p50', self.value_at_p50),
            ('p75', self.value_at_p75),
            ('p90', self.value_at_p90),
            ('p95', self.value_at_p95),
            ('p99', self.value_at_p99),
            ('p99.5', self.value_at_p99_5),
            ('p99.9', self.value_at_p99_9),
            ('p99.99', self.value_at_p99_99),
            ('p99.999', self.value_at_p99_999),
            ('p99.9999', self.value_at_p99_999_9),
        )
        results: dict[str, int] = {}
        for key, getter in getters:
            value = getter()
            if value is None:
                return None
            results[key] = value
        return results

    def _try_add_ns_to_total_and_update_minmax(self, time_in_ns: int) -> bool:
        if self._has_overflowed:
            return False
        if time_in_ns > UINT64_MAX - self._event_time_total:
            self._has_overflowed = True
            return False

        self._event_time_total += time_in_ns

        if self._event_count == 0:
            self._min_event_time = time_in_ns
            self._max_event_time = time_in_ns
        else:
            if time_in_ns < self._min_event_time:
                self._min_event_time = time_in_ns
            if time_in_ns > self._max_event_time:
                self._max_event_time = time_in_ns

        return True

    def _value_at_target_rank(self, target_rank: int) -> int | None:
        if self._event_count == 0:
            return None

        accumulated = 0
        for i in range(BUCKET_COUNT):
            count = self._buckets[i]
            if count > 0:
                prev_accumulated = accumulated
                accumulated += count
                if accumulated >= target_rank:
                    return self._value_at_target_rank_in_bucket(
                        i, count, prev_accumulated, target_rank
                    )

        return self._max_event_time

    def _value_at_target_rank_in_bucket(
        self,
        bucket_index: int,
        count: int,
        prev_accumulated: int,
        target_rank: int,
    ) -> int:
        bucket = _bucket_range(bucket_index)
        if bucket is None:
            lower, upper = 0, UINT64_MAX
        else:
            lower, upper = bucket

        if target_rank <= prev_accumulated:
            interpolated = lower
        else:
            target_offset = target_rank - prev_accumulated
            if bucket_index == BUCKET_COUNT - 1:
                range_width = UINT64_MAX - lower
            else:
                range_width = upper - lower

            if range_width <= UINT64_MAX // target_offset:
                interpolated = lower + (range_width * target_offset) // count
            else:
                interpolated = _u64_add_mul_div(
                    lower, range_width, target_offset, count
                )

        interpolated = max(interpolated, self._min_event_time)
        interpolated = min(interpolated, self._max_event_time)
        return interpolated

    def _value_at_percentile_in_bucket(
        self,
        bucket_index: int,
        count: int,
        prev_accumulated: int,
        target_rank: float,
    ) -> int:
        bucket = _bucket_range(bucket_index)
        if bucket is None:
            lower, upper = 0, UINT64_MAX
        else:
            lower, upper = bucket

        target_offset = target_rank - float(prev_accumulated)
        if bucket_index == BUCKET_COUNT - 1:
            range_width = float(UINT64_MAX - lower)
        else:
            range_width = float(upper - lower)

        fraction = target_offset / float(count)
        interpolated = float(lower) + (range_width * fraction)
        result = _llround(interpolated)

        result = max(result, self._min_event_time)
        result = min(result, self._max_event_time)
        return result


def _clamp_percentile(percentile: float) -> float:
    if percentile < 0.0:
        return 0.0
    if percentile > 100.0:
        return 100.0
    return percentile
