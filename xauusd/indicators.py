"""Indicators, pure stdlib. Every series returned is index-aligned with the
input bars, and every value is computable using ONLY bars at or before that
index. No exceptions, no "it's basically the same" - lookahead is fraud.
"""

from __future__ import annotations

from bisect import bisect_left, insort

from .data import Bar

Series = list[float | None]


def sma(values: list[float], period: int) -> Series:
    if period <= 0:
        raise ValueError("period must be positive")
    out: Series = [None] * len(values)
    total = 0.0
    for i, v in enumerate(values):
        total += v
        if i >= period:
            total -= values[i - period]
        if i >= period - 1:
            out[i] = total / period
    return out


def ema(values: list[float], period: int) -> Series:
    """EMA seeded with the SMA of the first `period` values."""
    if period <= 0:
        raise ValueError("period must be positive")
    out: Series = [None] * len(values)
    if len(values) < period:
        return out
    k = 2.0 / (period + 1.0)
    prev = sum(values[:period]) / period
    out[period - 1] = prev
    for i in range(period, len(values)):
        prev = values[i] * k + prev * (1.0 - k)
        out[i] = prev
    return out


def true_range(bars: list[Bar]) -> Series:
    out: Series = [None] * len(bars)
    for i in range(1, len(bars)):
        prev_close = bars[i - 1].close
        out[i] = max(
            bars[i].high - bars[i].low,
            abs(bars[i].high - prev_close),
            abs(bars[i].low - prev_close),
        )
    return out


def atr(bars: list[Bar], period: int = 14) -> Series:
    """Wilder's ATR."""
    tr = true_range(bars)
    out: Series = [None] * len(bars)
    if len(bars) < period + 1:
        return out
    seed = sum(t for t in tr[1 : period + 1] if t is not None) / period
    out[period] = seed
    prev = seed
    for i in range(period + 1, len(bars)):
        t = tr[i] or 0.0
        prev = (prev * (period - 1) + t) / period
        out[i] = prev
    return out


def rolling_max(values: list[float], period: int, shift: int = 0) -> Series:
    """Max of the `period` values ending `shift` bars before the current one.

    shift=1 gives "highest high of the previous N bars, excluding this one".
    """
    out: Series = [None] * len(values)
    for i in range(len(values)):
        end = i - shift + 1
        start = end - period
        if start < 0 or end <= start:
            continue
        out[i] = max(values[start:end])
    return out


def rolling_min(values: list[float], period: int, shift: int = 0) -> Series:
    out: Series = [None] * len(values)
    for i in range(len(values)):
        end = i - shift + 1
        start = end - period
        if start < 0 or end <= start:
            continue
        out[i] = min(values[start:end])
    return out


def rolling_percentile(values: Series, period: int, pct: float) -> Series:
    """Rolling percentile (linear interpolation) over a window ending at i.

    Maintains one incrementally sorted window instead of sorting per bar:
    O(n log period) compares plus a memmove, which is ~40x faster than the
    obvious version. Same numbers, less waiting - and waiting is the thing
    that stops you from running the walk-forward you should have run.
    """
    if not 0.0 <= pct <= 1.0:
        raise ValueError("pct must be in [0, 1]")
    if period <= 0:
        raise ValueError("period must be positive")
    out: Series = [None] * len(values)
    window: list[float] = []
    min_obs = max(10, period // 2)
    for i, v in enumerate(values):
        if v is not None:
            insort(window, v)
        drop = i - period
        if drop >= 0:
            old = values[drop]
            if old is not None:
                del window[bisect_left(window, old)]
        if i < period - 1 or len(window) < min_obs:
            continue
        pos = pct * (len(window) - 1)
        lo = int(pos)
        hi = min(lo + 1, len(window) - 1)
        out[i] = window[lo] + (window[hi] - window[lo]) * (pos - lo)
    return out


def swing_low(bars: list[Bar], left: int = 2, right: int = 2) -> list[bool]:
    """Fractal swing lows. Confirmed only `right` bars later, so the flag is
    written at the CONFIRMATION index, not at the pivot - that is what a live
    system can actually see.
    """
    out = [False] * len(bars)
    for i in range(left, len(bars) - right):
        pivot = bars[i].low
        if all(bars[j].low > pivot for j in range(i - left, i)) and all(
            bars[j].low >= pivot for j in range(i + 1, i + right + 1)
        ):
            out[i + right] = True
    return out


def swing_high(bars: list[Bar], left: int = 2, right: int = 2) -> list[bool]:
    out = [False] * len(bars)
    for i in range(left, len(bars) - right):
        pivot = bars[i].high
        if all(bars[j].high < pivot for j in range(i - left, i)) and all(
            bars[j].high <= pivot for j in range(i + 1, i + right + 1)
        ):
            out[i + right] = True
    return out


def slope(series: Series, lookback: int = 3) -> Series:
    """Simple change over `lookback` bars."""
    out: Series = [None] * len(series)
    for i in range(lookback, len(series)):
        a, b = series[i], series[i - lookback]
        if a is not None and b is not None:
            out[i] = a - b
    return out
