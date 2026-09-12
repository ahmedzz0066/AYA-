"""Bar data: loading, resampling, and a synthetic generator for smoke tests."""

from __future__ import annotations

import csv
import math
import random
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone


@dataclass(slots=True, frozen=True)
class Bar:
    """One OHLC bar. Prices are MID prices; spread is applied by the broker."""

    ts: datetime  # bar OPEN time, UTC
    open: float
    high: float
    low: float
    close: float
    volume: float = 0.0

    @property
    def range(self) -> float:
        return self.high - self.low


_TS_FORMATS = (
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%d %H:%M",
    "%Y-%m-%dT%H:%M:%S",
    "%Y-%m-%dT%H:%M:%S%z",
    "%Y.%m.%d %H:%M:%S",
    "%Y.%m.%d %H:%M",
    "%d/%m/%Y %H:%M:%S",
    "%d.%m.%Y %H:%M:%S",
)


def parse_ts(raw: str) -> datetime:
    """Parse the timestamp spellings brokers actually emit."""
    raw = raw.strip().replace("﻿", "")
    if raw.isdigit():  # epoch seconds or millis
        val = int(raw)
        if val > 10_000_000_000:
            val //= 1000
        return datetime.fromtimestamp(val, tz=timezone.utc)
    for fmt in _TS_FORMATS:
        try:
            dt = datetime.strptime(raw, fmt)
        except ValueError:
            continue
        return dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt.astimezone(timezone.utc)
    # MT5 exports sometimes split date and time into two columns already joined by tab
    try:
        return datetime.fromisoformat(raw).replace(tzinfo=timezone.utc)
    except ValueError as exc:  # pragma: no cover - defensive
        raise ValueError(f"unrecognised timestamp: {raw!r}") from exc


def load_csv(path: str, tz_shift_hours: float = 0.0) -> list[Bar]:
    """Load OHLC bars from CSV.

    Accepts headered or headerless files. Columns are matched by name when a
    header exists, otherwise assumed to be time,open,high,low,close[,volume].
    MT5 files that split date and time into two columns are handled too.

    tz_shift_hours: add this to every timestamp to convert broker server time
    to UTC (e.g. a GMT+2 broker needs -2.0). Session filters assume UTC.
    """
    bars: list[Bar] = []
    with open(path, newline="", encoding="utf-8-sig") as fh:
        sample = fh.read(4096)
        fh.seek(0)
        try:
            dialect = csv.Sniffer().sniff(sample, delimiters=",;\t")
        except csv.Error:
            dialect = csv.excel
        reader = csv.reader(fh, dialect)
        rows = [r for r in reader if r and any(c.strip() for c in r)]

    if not rows:
        raise ValueError(f"{path} contains no data rows")

    header: list[str] | None = None
    first = [c.strip().lower() for c in rows[0]]
    if any(tok in first for tok in ("open", "<open>", "time", "date", "<date>")):
        header = [c.strip().lower().strip("<>") for c in rows[0]]
        rows = rows[1:]

    def idx(*names: str) -> int | None:
        if header is None:
            return None
        for name in names:
            if name in header:
                return header.index(name)
        return None

    i_date = idx("date", "time", "datetime", "timestamp")
    i_time = idx("time") if i_date is not None and header and header[i_date] != "time" else None
    i_open = idx("open")
    i_high = idx("high")
    i_low = idx("low")
    i_close = idx("close", "close/last")
    i_vol = idx("volume", "tickvol", "vol")

    shift = timedelta(hours=tz_shift_hours)
    for row in rows:
        if header is None or i_open is None:
            # positional fallback; detect the MT5 two-column date/time layout
            if len(row) >= 7 and ":" in row[1] and "-" not in row[1] and row[1].count(":") >= 1 and not _is_float(row[1]):
                ts = parse_ts(f"{row[0].strip()} {row[1].strip()}")
                o, h, l, c = (float(row[i]) for i in (2, 3, 4, 5))
                v = float(row[6]) if len(row) > 6 and _is_float(row[6]) else 0.0
            else:
                ts = parse_ts(row[0])
                o, h, l, c = (float(row[i]) for i in (1, 2, 3, 4))
                v = float(row[5]) if len(row) > 5 and _is_float(row[5]) else 0.0
        else:
            if i_time is not None:
                ts = parse_ts(f"{row[i_date].strip()} {row[i_time].strip()}")
            else:
                ts = parse_ts(row[i_date])
            o = float(row[i_open])
            h = float(row[i_high])
            l = float(row[i_low])
            c = float(row[i_close])
            v = float(row[i_vol]) if i_vol is not None and _is_float(row[i_vol]) else 0.0
        bars.append(Bar(ts + shift, o, h, l, c, v))

    bars.sort(key=lambda b: b.ts)
    return dedupe(bars)


def _is_float(text: str) -> bool:
    try:
        float(text)
    except (TypeError, ValueError):
        return False
    return True


def dedupe(bars: list[Bar]) -> list[Bar]:
    """Drop duplicate timestamps, keeping the last occurrence."""
    out: list[Bar] = []
    for bar in bars:
        if out and out[-1].ts == bar.ts:
            out[-1] = bar
        else:
            out.append(bar)
    return out


def resample(bars: list[Bar], minutes: int) -> list[Bar]:
    """Aggregate M5 bars up to a higher timeframe (e.g. 60 for H1).

    Buckets are aligned to the epoch, so H1 buckets start on the hour.
    """
    if minutes <= 0:
        raise ValueError("minutes must be positive")
    step = minutes * 60
    out: list[Bar] = []
    bucket_start: int | None = None
    o = h = l = c = 0.0
    vol = 0.0
    for bar in bars:
        epoch = int(bar.ts.timestamp())
        start = epoch - (epoch % step)
        if bucket_start is None or start != bucket_start:
            if bucket_start is not None:
                out.append(Bar(datetime.fromtimestamp(bucket_start, tz=timezone.utc), o, h, l, c, vol))
            bucket_start = start
            o, h, l, c, vol = bar.open, bar.high, bar.low, bar.close, bar.volume
        else:
            h = max(h, bar.high)
            l = min(l, bar.low)
            c = bar.close
            vol += bar.volume
    if bucket_start is not None:
        out.append(Bar(datetime.fromtimestamp(bucket_start, tz=timezone.utc), o, h, l, c, vol))
    return out


def htf_index(bars: list[Bar], minutes: int) -> list[int]:
    """For each M5 bar, the index of the last CLOSED higher-timeframe bar.

    -1 means no higher-timeframe bar has closed yet. This mapping is the one
    place where a lookahead bug silently doubles your backtest returns, so it
    lives here, alone, and is unit-tested.
    """
    htf = resample(bars, minutes)
    step = minutes * 60
    out: list[int] = []
    cursor = -1
    for bar in bars:
        epoch = int(bar.ts.timestamp())
        current_start = epoch - (epoch % step)
        while cursor + 1 < len(htf) and int(htf[cursor + 1].ts.timestamp()) + step <= current_start:
            cursor += 1
        out.append(cursor)
    return out


def synthetic(
    n_bars: int = 60_000,
    start: datetime | None = None,
    seed: int = 7,
    start_price: float = 2400.0,
) -> list[Bar]:
    """Generate synthetic M5 gold-ish bars.

    This exists ONLY to smoke-test the plumbing. Synthetic data has no edge in
    it, so any performance measured on it is meaningless. Use real M5 data.
    """
    rng = random.Random(seed)
    if start is None:
        start = datetime(2023, 1, 2, 0, 0, tzinfo=timezone.utc)
    price = start_price
    bars: list[Bar] = []
    ts = start
    drift = 0.0
    trend_left = 0
    while len(bars) < n_bars:
        # skip the weekend: gold is closed Fri 21:00 UTC -> Sun 22:00 UTC
        if ts.weekday() == 5 or (ts.weekday() == 4 and ts.hour >= 21) or (ts.weekday() == 6 and ts.hour < 22):
            ts += timedelta(minutes=5)
            continue
        # intraday volatility seasonality: London + NY overlap is where gold lives
        hour = ts.hour + ts.minute / 60.0
        seasonal = 0.35 + 0.9 * math.exp(-((hour - 9.0) ** 2) / 8.0) + 1.0 * math.exp(-((hour - 14.5) ** 2) / 6.0)
        sigma = 0.55 * seasonal  # ~$ per 5m bar
        if trend_left <= 0:
            trend_left = rng.randint(12, 160)
            drift = rng.gauss(0.0, 0.09)
        trend_left -= 1
        o = price
        steps = [rng.gauss(drift / 5.0, sigma / math.sqrt(5.0)) for _ in range(5)]
        path = [o]
        for s in steps:
            path.append(path[-1] + s)
        c = path[-1]
        h = max(path) + abs(rng.gauss(0, sigma * 0.18))
        l = min(path) - abs(rng.gauss(0, sigma * 0.18))
        bars.append(Bar(ts, round(o, 2), round(h, 2), round(l, 2), round(c, 2), rng.randint(50, 900)))
        price = c
        ts += timedelta(minutes=5)
    return bars


def write_csv(bars: list[Bar], path: str) -> None:
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["time", "open", "high", "low", "close", "volume"])
        for b in bars:
            w.writerow([b.ts.strftime("%Y-%m-%d %H:%M:%S"), b.open, b.high, b.low, b.close, b.volume])
