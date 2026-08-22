"""
al-Mizan li-l-Dhahab  --  The Balance for Gold.

A reference implementation of the twelve-step supply/demand algorithm described in
docs/KITAB_AL_MIZAN_LI_AL_DHAHAB.md, for day trading XAUUSD.

The module is dependency-free and pure: it consumes OHLC candles and returns ranked
zones plus a fully specified trade plan (entry, stop, targets, size).

Usage:
    python3 algorithm/mizan.py --selftest
    python3 algorithm/mizan.py --csv m15.csv [--h4 h4.csv] [--d1 d1.csv] \
        [--equity 10000] [--risk 0.5]

CSV columns (header required): time,open,high,low,close
`time` is ISO-8601; naive timestamps are assumed to be UTC.
"""

from __future__ import annotations

import argparse
import csv
import sys
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Sequence, Tuple

# ----------------------------------------------------------------------------------
# Step 0 -- constants of measure.  Every distance is expressed in units of ATR (A)
# so that the method is invariant under gold's volatility regimes.
# ----------------------------------------------------------------------------------

PARAMS: Dict[str, float] = {
    "atr_period": 14,
    "base_max_len": 5,
    "base_height_atr": 0.60,       # Step 2.1
    "base_body_ratio": 0.50,       # Step 2.2
    "base_single_range_atr": 0.35, # Step 2.2 (single-candle base alternative)
    "base_overlap": 0.50,          # Step 2.3
    "displacement_atr": 2.0,       # Step 3.1
    "conviction_body_ratio": 0.60, # Step 3.2
    "conviction_wick_ratio": 0.25, # Step 3.2
    "fvg_min_atr": 0.20,           # Step 3.4
    "fvg_min_abs": 0.60,           # Step 3.4 -- absolute floor in USD for gold
    "sweep_lookback": 12,          # Step 4.3
    "swing_wing": 2,               # fractal wing for swing points
    "stop_buffer_atr": 0.15,       # Step 9.1
    "stop_buffer_abs": 1.20,       # Step 9.1
    "spread": 0.30,                # Step 9.1 -- gold spread in USD
    "min_rr": 3.0,                 # Step 10.2
    "grade_a": 80.0,               # Step 6
    "grade_b": 65.0,               # Step 6
    "magazine_atr": 0.25,          # Step 6, criterion 7
    "contract_size": 100.0,        # 1.00 lot XAUUSD = 100 oz
}

# Session boundaries, UTC hours (Step 0 / Section VII.3).
ASIA = (23, 6)          # wraps midnight
LONDON_KILL = (7, 10)
NY_KILL_START = (12, 30)
NY_KILL_END = (16, 0)
NO_NEW_ENTRY_HOUR = 17
FLAT_HOUR = 20


@dataclass(frozen=True)
class Candle:
    ts: datetime
    o: float
    h: float
    l: float
    c: float
    v: float = 0.0

    @property
    def range(self) -> float:
        return max(self.h - self.l, 1e-9)

    @property
    def body(self) -> float:
        return abs(self.c - self.o)

    @property
    def body_ratio(self) -> float:
        return self.body / self.range

    @property
    def bullish(self) -> bool:
        return self.c >= self.o

    @property
    def upper_wick(self) -> float:
        return self.h - max(self.o, self.c)

    @property
    def lower_wick(self) -> float:
        return min(self.o, self.c) - self.l


@dataclass
class Zone:
    side: str                 # "demand" | "supply"
    pattern: str              # DBR | RBR | RBD | DBD
    form: str                 # "I" | "II" | "III"
    base_start: int
    base_end: int
    departure_end: int
    formed_at: datetime
    distal: float
    proximal_body: float
    proximal_wick: float
    displacement: float
    fvg_width: float
    swept: bool
    broke_structure: bool
    taps: int = 0
    destroyed: bool = False
    atr_at_formation: float = 0.0
    score: float = 0.0
    grade: str = "-"
    components: Dict[str, float] = field(default_factory=dict)

    @property
    def height(self) -> float:
        return abs(self.distal - self.proximal_wick)

    def __str__(self) -> str:  # pragma: no cover - presentation only
        return (
            f"[{self.grade}] {self.side:6s} {self.pattern} form={self.form:3s} "
            f"score={self.score:5.1f} zone={min(self.distal, self.proximal_body):.2f}"
            f"-{max(self.distal, self.proximal_body):.2f} "
            f"disp={self.displacement:.2f} fvg={self.fvg_width:.2f} "
            f"taps={self.taps} born={self.formed_at:%Y-%m-%d %H:%M}Z"
        )


# ----------------------------------------------------------------------------------
# Instruments of measure
# ----------------------------------------------------------------------------------

def atr_series(candles: Sequence[Candle], period: int = 14) -> List[float]:
    """Wilder's ATR.  Values before `period` are seeded with the running mean."""
    trs: List[float] = []
    for i, c in enumerate(candles):
        if i == 0:
            trs.append(c.h - c.l)
        else:
            pc = candles[i - 1].c
            trs.append(max(c.h - c.l, abs(c.h - pc), abs(c.l - pc)))
    out: List[float] = []
    running = 0.0
    for i, tr in enumerate(trs):
        if i < period:
            running = (running * i + tr) / (i + 1)
            out.append(running)
        else:
            out.append((out[-1] * (period - 1) + tr) / period)
    return out


def swing_points(candles: Sequence[Candle], wing: int = 2) -> Tuple[List[int], List[int]]:
    """Fractal swing highs and lows confirmed by `wing` candles on each side."""
    highs, lows = [], []
    for i in range(wing, len(candles) - wing):
        window = candles[i - wing: i + wing + 1]
        if candles[i].h == max(w.h for w in window) and candles[i].h > candles[i - 1].h:
            highs.append(i)
        if candles[i].l == min(w.l for w in window) and candles[i].l < candles[i - 1].l:
            lows.append(i)
    return highs, lows


def structure_bias(candles: Sequence[Candle], wing: int = 2) -> int:
    """Step 1.1/1.2 -- +1 bullish, -1 bearish, 0 neutral, by last break of structure."""
    if len(candles) < 4 * wing + 2:
        return 0
    highs, lows = swing_points(candles, wing)
    bias = 0
    hi_ptr = lo_ptr = 0
    last_high: Optional[float] = None
    last_low: Optional[float] = None
    for i, c in enumerate(candles):
        while hi_ptr < len(highs) and highs[hi_ptr] + wing <= i:
            last_high = candles[highs[hi_ptr]].h
            hi_ptr += 1
        while lo_ptr < len(lows) and lows[lo_ptr] + wing <= i:
            last_low = candles[lows[lo_ptr]].l
            lo_ptr += 1
        if last_high is not None and c.c > last_high:
            bias = 1
            last_high = None
        elif last_low is not None and c.c < last_low:
            bias = -1
            last_low = None
    return bias


def combine_bias(d1: int, h4: int) -> int:
    """Step 1.3 -- 0 means conflict (Form III only, half size)."""
    if d1 == h4:
        return d1
    if d1 == 0:
        return h4
    if h4 == 0:
        return d1
    return 0


def largest_fvg(candles: Sequence[Candle], lo: int, hi: int, bullish: bool) -> float:
    """Step 3.4 -- widest three-candle inefficiency inside [lo, hi]."""
    best = 0.0
    for i in range(max(lo + 1, 1), min(hi, len(candles) - 1)):
        if bullish:
            gap = candles[i + 1].l - candles[i - 1].h
        else:
            gap = candles[i - 1].l - candles[i + 1].h
        best = max(best, gap)
    return best


# ----------------------------------------------------------------------------------
# Steps 2-4 -- base, departure, geometry
# ----------------------------------------------------------------------------------

def is_base(candles: Sequence[Candle], j: int, k: int, atr: float) -> bool:
    base = candles[j: k + 1]
    height = max(c.h for c in base) - min(c.l for c in base)
    if height > PARAMS["base_height_atr"] * atr:
        return False
    if len(base) == 1:
        c = base[0]
        return c.body_ratio <= PARAMS["base_body_ratio"] or c.range <= PARAMS["base_single_range_atr"] * atr
    if sum(c.body_ratio for c in base) / len(base) > PARAMS["base_body_ratio"]:
        return False
    anchor = base[0]
    for c in base[1:]:
        overlap = min(anchor.h, c.h) - max(anchor.l, c.l)
        if overlap < PARAMS["base_overlap"] * c.range:
            return False
    return True


def _leg_direction(candles: Sequence[Candle], j: int) -> int:
    """Direction of the leg *into* the base (up to 3 candles before it)."""
    start = max(0, j - 3)
    if start >= j:
        return 0
    net = candles[j - 1].c - candles[start].o
    return 1 if net > 0 else (-1 if net < 0 else 0)


def _swept_liquidity(candles: Sequence[Candle], base_start: int, base_end: int, bullish: bool) -> bool:
    """Step 4.3 -- was the base built on the far side of a raided swing extreme?

    The raid may be the base itself or one of the three candles immediately before it;
    the level raided must be an extreme established *before* that window, and price must
    have closed back through it (the sweep is reclaimed, not merely extended).
    """
    look = int(PARAMS["sweep_lookback"])
    win_start = max(0, base_start - 3)
    prior_lo = max(0, win_start - look)
    prior = candles[prior_lo:win_start]
    if len(prior) < 3 or win_start >= base_end + 1:
        return False
    window = candles[win_start: base_end + 1]
    if bullish:
        level = min(c.l for c in prior)
        raided = min(c.l for c in window) < level
        reclaimed = max(c.c for c in window) > level
    else:
        level = max(c.h for c in prior)
        raided = max(c.h for c in window) > level
        reclaimed = min(c.c for c in window) < level
    return bool(raided and reclaimed)


def _broke_structure(candles: Sequence[Candle], base_start: int, dep_end: int, bullish: bool, wing: int) -> bool:
    """Step 3.3 -- the departure must *close* beyond the most recent swing point.

    In a one-sided market no fractal swing may exist in the direction of travel; the
    reference is then the extreme of the candles preceding the base.
    """
    highs, lows = swing_points(candles[: dep_end + 1], wing)
    close = candles[dep_end].c
    look = int(PARAMS["sweep_lookback"])
    prior = candles[max(0, base_start - look): base_start]
    if bullish:
        refs = [candles[i].h for i in highs if i + wing <= dep_end]
        ref = refs[-1] if refs else (max((c.h for c in prior), default=None))
        return ref is not None and close > ref
    refs = [candles[i].l for i in lows if i + wing <= dep_end]
    ref = refs[-1] if refs else (min((c.l for c in prior), default=None))
    return ref is not None and close < ref


def _count_taps(candles: Sequence[Candle], zone: Zone) -> Tuple[int, bool]:
    """Step 5 -- contiguous runs of contact count as one tap; a close beyond distal kills."""
    taps = 0
    inside = False
    for c in candles[zone.departure_end + 1:]:
        if zone.side == "demand":
            touch = c.l <= zone.proximal_wick
            dead = c.c < zone.distal
        else:
            touch = c.h >= zone.proximal_wick
            dead = c.c > zone.distal
        if touch and not inside:
            taps += 1
            inside = True
        elif not touch:
            inside = False
        if dead:
            return taps, True
    return taps, False


def detect_zones(candles: Sequence[Candle], atr: Optional[List[float]] = None) -> List[Zone]:
    """Steps 2-5 -- every zone that survives the gates, with taps and destruction marked."""
    if atr is None:
        atr = atr_series(candles, int(PARAMS["atr_period"]))
    wing = int(PARAMS["swing_wing"])
    zones: List[Zone] = []
    n = len(candles)

    for j in range(3, n - 2):
        for length in range(1, int(PARAMS["base_max_len"]) + 1):
            k = j + length - 1
            if k + 1 >= n:
                break
            a = atr[k]
            if a <= 0 or not is_base(candles, j, k, a):
                continue

            base = candles[j: k + 1]
            base_high = max(c.h for c in base)
            base_low = min(c.l for c in base)
            prox_body_up = max(max(c.o, c.c) for c in base)
            prox_body_dn = min(min(c.o, c.c) for c in base)

            for span in range(1, 4):
                dep_end = k + span
                if dep_end >= n:
                    break
                close = candles[dep_end].c
                up_disp = close - prox_body_up
                dn_disp = prox_body_dn - close
                bullish = up_disp >= dn_disp
                displacement = up_disp if bullish else dn_disp
                if displacement < PARAMS["displacement_atr"] * a:
                    continue

                dep = candles[k + 1: dep_end + 1]
                conviction = any(
                    c.body_ratio >= PARAMS["conviction_body_ratio"]
                    and c.bullish == bullish
                    and (c.upper_wick if bullish else c.lower_wick) <= PARAMS["conviction_wick_ratio"] * c.range
                    for c in dep
                )
                if not conviction:
                    continue

                fvg = largest_fvg(candles, j, dep_end, bullish)
                if fvg < max(PARAMS["fvg_min_atr"] * a, PARAMS["fvg_min_abs"]):
                    continue

                bos = _broke_structure(candles, j, dep_end, bullish, wing)
                if not bos:
                    continue

                inbound = _leg_direction(candles, j)
                if bullish:
                    pattern = "DBR" if inbound < 0 else "RBR"
                    side = "demand"
                    distal, prox_body, prox_wick = base_low, prox_body_up, base_high
                else:
                    pattern = "RBD" if inbound > 0 else "DBD"
                    side = "supply"
                    distal, prox_body, prox_wick = base_high, prox_body_dn, base_low

                swept = _swept_liquidity(candles, j, k, bullish)
                form = "III" if swept else ("I" if pattern in ("DBR", "RBD") else "II")

                zone = Zone(
                    side=side, pattern=pattern, form=form,
                    base_start=j, base_end=k, departure_end=dep_end,
                    formed_at=candles[dep_end].ts,
                    distal=distal, proximal_body=prox_body, proximal_wick=prox_wick,
                    displacement=displacement, fvg_width=fvg, swept=swept,
                    broke_structure=bos, atr_at_formation=a,
                )
                zone.taps, zone.destroyed = _count_taps(candles, zone)
                zones.append(zone)
                break  # the first qualifying departure span defines the zone
            else:
                continue
            break  # one zone per base start

    return _dedupe(zones)


def _dedupe(zones: Sequence[Zone]) -> List[Zone]:
    """Two bases at one price are one order.  Keep the strongest of any overlapping pair."""
    kept: List[Zone] = []
    for z in sorted(zones, key=lambda x: (-x.displacement, x.base_start)):
        clash = False
        for k in kept:
            if k.side != z.side:
                continue
            lo = max(min(k.distal, k.proximal_wick), min(z.distal, z.proximal_wick))
            hi = min(max(k.distal, k.proximal_wick), max(z.distal, z.proximal_wick))
            overlap = max(0.0, hi - lo)
            if overlap >= 0.70 * min(k.height, z.height):
                clash = True
                break
        if not clash:
            kept.append(z)
    kept.sort(key=lambda x: x.base_start)
    return kept


# ----------------------------------------------------------------------------------
# Step 6 -- the Balance (al-Mizan)
# ----------------------------------------------------------------------------------

def _in_session(ts: datetime, start: Tuple[int, int], end: Tuple[int, int]) -> bool:
    t = ts.astimezone(timezone.utc)
    minutes = t.hour * 60 + t.minute
    s = start[0] * 60 + start[1]
    e = end[0] * 60 + end[1]
    return s <= minutes < e if s <= e else (minutes >= s or minutes < e)


def in_asian_session(ts: datetime) -> bool:
    return _in_session(ts, (ASIA[0], 0), (ASIA[1], 0))


def magazine_weight(price: float) -> int:
    """Section VII.2 -- psychological magazines, ranked."""
    for step, weight in ((100.0, 3), (50.0, 2), (25.0, 1), (10.0, 1)):
        if abs(price - round(price / step) * step) <= 0.001:
            return weight
    return 0


def nearest_magazine(price: float) -> Tuple[float, int]:
    best = (0.0, 0)
    best_dist = float("inf")
    for step, weight in ((100.0, 3), (50.0, 2), (25.0, 1), (10.0, 1)):
        level = round(price / step) * step
        d = abs(price - level)
        if d < best_dist or (abs(d - best_dist) < 1e-9 and weight > best[1]):
            best_dist, best = d, (level, weight)
    return best


def score_zone(
    zone: Zone,
    bias: int,
    htf_zone_overlap: bool = False,
    asian_range: Optional[Tuple[float, float]] = None,
) -> Zone:
    """Assign the eight components of the Mizan and the resulting grade."""
    a = zone.atr_at_formation or 1.0
    comp: Dict[str, float] = {}

    # 1. departure strength
    comp["departure"] = min(20.0, 10.0 * (zone.displacement / (PARAMS["displacement_atr"] * a)))

    # 2. base quality
    base_len = zone.base_end - zone.base_start + 1
    if base_len <= 2 and zone.height <= 0.35 * a:
        comp["base"] = 15.0
    elif base_len <= 2:
        comp["base"] = 12.0
    elif base_len == 3:
        comp["base"] = 10.0
    else:
        comp["base"] = 5.0

    # 3. imbalance width
    comp["imbalance"] = min(15.0, 15.0 * (zone.fvg_width / (0.5 * a)))

    # 4. liquidity sweep
    comp["sweep"] = 15.0 if zone.swept else (7.0 if zone.broke_structure else 0.0)

    # 5. higher-timeframe alignment
    polarity = 1 if zone.side == "demand" else -1
    if bias == 0:
        comp["htf"] = 0.0
    elif polarity == bias:
        comp["htf"] = 15.0 if htf_zone_overlap else 10.0
    else:
        comp["htf"] = -25.0

    # 6. freshness
    comp["freshness"] = 10.0 if zone.taps == 0 else (4.0 if zone.taps == 1 else -100.0)

    # 7. psychological magazine
    level, weight = nearest_magazine(zone.proximal_body)
    comp["magazine"] = (5.0 * weight / 3.0) if abs(zone.proximal_body - level) <= PARAMS["magazine_atr"] * a else 0.0

    # 8. session of birth
    ts = zone.formed_at
    born_in_asia_interior = False
    if asian_range and in_asian_session(ts):
        lo, hi = min(asian_range), max(asian_range)
        born_in_asia_interior = lo < zone.proximal_body < hi
    if born_in_asia_interior:
        comp["session"] = 0.0
    elif _in_session(ts, (LONDON_KILL[0], 0), (LONDON_KILL[1], 0)) or _in_session(ts, NY_KILL_START, NY_KILL_END):
        comp["session"] = 5.0
    elif in_asian_session(ts):
        comp["session"] = 0.0
    else:
        comp["session"] = 2.0

    zone.components = comp
    zone.score = round(sum(comp.values()), 1)
    if zone.destroyed or zone.taps >= 2:
        zone.grade, zone.score = "DEAD", 0.0
    elif zone.score >= PARAMS["grade_a"]:
        zone.grade = "A"
    elif zone.score >= PARAMS["grade_b"]:
        zone.grade = "B"
    else:
        zone.grade = "-"
    return zone


# ----------------------------------------------------------------------------------
# Step 7 -- selection;  Steps 8-11 -- the plan
# ----------------------------------------------------------------------------------

_FORM_RANK = {"III": 0, "I": 1, "II": 2}


def select_zones(zones: Sequence[Zone], price: float, bias: int, atr_d1: float) -> List[Zone]:
    live = [
        z for z in zones
        if z.grade in ("A", "B")
        and not z.destroyed
        and abs(z.proximal_body - price) <= 1.5 * atr_d1
        and ((z.side == "demand" and z.proximal_body < price) or (z.side == "supply" and z.proximal_body > price))
        and ((bias == 0 and z.form == "III") or (bias == 1 and z.side == "demand") or (bias == -1 and z.side == "supply"))
    ]
    live.sort(key=lambda z: (-z.score, _FORM_RANK[z.form], z.taps, abs(z.proximal_body - price)))
    best: List[Zone] = []
    for side in ("demand", "supply"):
        for z in live:
            if z.side == side:
                best.append(z)
                break
    return best


@dataclass
class TradePlan:
    zone: Zone
    entry_mode: str
    entry: float
    stop: float
    risk_per_unit: float
    t1: float
    t2: Optional[float]
    t3: Optional[float]
    rr_to_t3: Optional[float]
    lots: float
    notes: List[str] = field(default_factory=list)
    valid: bool = True

    def __str__(self) -> str:  # pragma: no cover - presentation only
        head = "TRADE" if self.valid else "NO TRADE"
        body = (
            f"{head}: {self.zone.side} via {self.entry_mode} | entry {self.entry:.2f} "
            f"stop {self.stop:.2f} (R={self.risk_per_unit:.2f}) T1 {self.t1:.2f}"
        )
        if self.t2 is not None:
            body += f" T2 {self.t2:.2f}"
        if self.t3 is not None:
            body += f" T3 {self.t3:.2f}"
        if self.rr_to_t3 is not None:
            body += f" (RR {self.rr_to_t3:.2f})"
        body += f" lots {self.lots:.2f}"
        return body + ("" if not self.notes else "\n  - " + "\n  - ".join(self.notes))


def build_plan(
    zone: Zone,
    atr: float,
    equity: float,
    risk_pct: float = 0.5,
    liquidity_target: Optional[float] = None,
    htf_opposing: Optional[float] = None,
    now: Optional[datetime] = None,
    news_block: bool = False,
) -> TradePlan:
    """Steps 8-11 -- entry mode, stop, targets, reward gate and size."""
    notes: List[str] = []
    valid = True

    entry_mode = "limit@proximal" if (zone.grade == "A" and zone.taps == 0) else "M1/M5 CHoCH confirmation"
    entry = zone.proximal_body
    buffer = max(PARAMS["stop_buffer_atr"] * atr, PARAMS["stop_buffer_abs"]) + PARAMS["spread"]
    stop = zone.distal - buffer if zone.side == "demand" else zone.distal + buffer
    r = abs(entry - stop)
    if r <= 0:
        return TradePlan(zone, entry_mode, entry, stop, 0.0, entry, None, None, None, 0.0,
                         ["degenerate zone: zero risk distance"], False)

    sign = 1 if zone.side == "demand" else -1
    t1 = entry + sign * 1.5 * r
    t2 = liquidity_target
    t3 = htf_opposing
    far = t3 if t3 is not None else (t2 if t2 is not None else t1)
    rr = abs(far - entry) / r

    if rr < PARAMS["min_rr"]:
        valid = False
        notes.append(f"Step 10.2 breached: best reward {rr:.2f}R < {PARAMS['min_rr']:.1f}R -- delete the trade, do not lower the target")
    if r > 0.8 * atr * 4:  # 0.8 x A_H4, approximated as 4 x A(M15) when H4 ATR is absent
        notes.append("Step 9.3: stop wider than 0.8 x A_H4 -- refine the zone on M5 or abandon it")
    if zone.taps >= 1:
        notes.append("Step 5.2: zone already tapped once -- confirmation entry only, no limit order")
    if news_block:
        valid = False
        notes.append("Step 0.5: inside a high-impact news block window -- the algorithm is halted")
    if now is not None:
        hour = now.astimezone(timezone.utc).hour
        if hour >= NO_NEW_ENTRY_HOUR:
            valid = False
            notes.append(f"Step 11.4: no new entries after {NO_NEW_ENTRY_HOUR}:00 UTC (flat by {FLAT_HOUR}:00 UTC)")

    lots = 0.0
    if valid:
        lots = round((equity * risk_pct / 100.0) / (r * PARAMS["contract_size"]), 2)
        if lots <= 0:
            valid = False
            notes.append("Step 11.2: computed size rounds to zero -- the risk unit is too small for this stop")

    return TradePlan(zone, entry_mode, entry, stop, r, t1, t2, t3, rr, lots, notes, valid)


# ----------------------------------------------------------------------------------
# Session helpers (Step 0.2)
# ----------------------------------------------------------------------------------

def asian_range(candles: Sequence[Candle], day: datetime) -> Optional[Tuple[float, float]]:
    """Asian range for the session ending on the morning of `day` (23:00 prev -> 06:00)."""
    end = day.astimezone(timezone.utc).replace(hour=6, minute=0, second=0, microsecond=0)
    start = end - timedelta(hours=7)
    window = [c for c in candles if start <= c.ts.astimezone(timezone.utc) < end]
    if not window:
        return None
    return (min(c.l for c in window), max(c.h for c in window))


# ----------------------------------------------------------------------------------
# I/O
# ----------------------------------------------------------------------------------

def load_csv(path: str) -> List[Candle]:
    out: List[Candle] = []
    with open(path, newline="") as fh:
        for row in csv.DictReader(fh):
            keys = {k.strip().lower(): v for k, v in row.items() if k}
            ts = datetime.fromisoformat(keys["time"].strip().replace("Z", "+00:00"))
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)
            out.append(Candle(ts, float(keys["open"]), float(keys["high"]),
                              float(keys["low"]), float(keys["close"]),
                              float(keys.get("volume") or 0.0)))
    out.sort(key=lambda c: c.ts)
    return out


def analyse(
    m15: Sequence[Candle],
    h4: Optional[Sequence[Candle]] = None,
    d1: Optional[Sequence[Candle]] = None,
    equity: float = 10_000.0,
    risk_pct: float = 0.5,
) -> Tuple[int, List[Zone], List[TradePlan]]:
    atr = atr_series(m15, int(PARAMS["atr_period"]))
    bias = combine_bias(
        structure_bias(d1) if d1 else 0,
        structure_bias(h4) if h4 else structure_bias(m15),
    )
    ar = asian_range(m15, m15[-1].ts)
    zones = [score_zone(z, bias, asian_range=ar) for z in detect_zones(m15, atr)]
    price = m15[-1].c
    atr_d1 = atr_series(d1, 14)[-1] if d1 else atr[-1] * 8
    chosen = select_zones(zones, price, bias, atr_d1)
    plans = [
        build_plan(
            z, atr[-1], equity, risk_pct,
            liquidity_target=(min(ar) if z.side == "supply" else max(ar)) if ar else None,
            htf_opposing=None, now=m15[-1].ts,
        )
        for z in chosen
    ]
    return bias, zones, plans


# ----------------------------------------------------------------------------------
# Self-test: a synthetic sweep-origin Drop-Base-Rally (Form III) on gold
# ----------------------------------------------------------------------------------

def _synthetic_m15() -> List[Candle]:
    """A textbook sweep-origin Drop-Base-Rally: balance, decline, swing low, bounce,
    raid of that low, reclaim, tight base, displacement leaving an FVG."""
    start = datetime(2026, 8, 20, 5, 0, tzinfo=timezone.utc)
    out: List[Candle] = []

    def add(o: float, h: float, l: float, c: float) -> None:
        out.append(Candle(start + timedelta(minutes=15 * len(out)), o, h, l, c))

    px = 2000.0
    for i in range(20):                                  # balance: establishes ATR ~ 2.5
        o, c = px, px + (0.6 if i % 2 == 0 else -0.6)
        add(o, max(o, c) + 0.7, min(o, c) - 0.7, c)
        px = c
    for _ in range(4):                                   # decline into the swing low
        o, c = px, px - 1.6
        add(o, o + 0.4, c - 0.5, c)
        px = c
    swing_low = px - 0.5
    for _ in range(3):                                   # bounce -- confirms the fractal low
        o, c = px, px + 1.4
        add(o, c + 0.5, o - 0.4, c)
        px = c
    o, c = px, px - 1.8                                  # rotation back down
    add(o, o + 0.4, c - 0.4, c)
    px = c
    o, c = px, swing_low + 0.6                           # the raid: takes the low, closes back above
    add(o, o + 0.3, swing_low - 2.2, c)
    px = c
    add(px, px + 0.5, px - 0.4, px + 0.1)                # base candle 1 (tight, small body)
    px += 0.1
    add(px, px + 0.45, px - 0.35, px - 0.05)             # base candle 2
    px -= 0.05
    add(px, px + 8.5, px - 0.2, px + 8.2)                # displacement candle 1
    px += 8.2
    add(px + 1.2, px + 7.0, px + 1.1, px + 6.6)          # displacement candle 2 -- leaves the FVG
    px += 6.6
    for _ in range(6):                                   # drift away; the zone stays fresh
        o, c = px, px + 0.5
        add(o, c + 0.8, o - 0.6, c)
        px = c
    return out


def _selftest() -> int:
    candles = _synthetic_m15()
    atr = atr_series(candles, 14)
    zones = detect_zones(candles, atr)
    demand = [z for z in zones if z.side == "demand"]
    assert demand, "no demand zone detected in the synthetic Drop-Base-Rally"
    z = max(demand, key=lambda x: x.displacement)
    assert z.pattern == "DBR", f"expected DBR, got {z.pattern}"
    assert z.swept and z.form == "III", f"expected sweep-origin Form III, got form {z.form}"
    assert z.fvg_width >= PARAMS["fvg_min_abs"], "imbalance gate not proved"
    assert z.taps == 0, f"expected a fresh zone, got {z.taps} taps"

    score_zone(z, bias=1, htf_zone_overlap=True)
    assert z.grade in ("A", "B"), f"expected a graded zone, got {z.grade} ({z.score})"

    plan = build_plan(z, atr[-1], equity=10_000, risk_pct=0.5,
                      liquidity_target=z.proximal_body + 40.0,
                      htf_opposing=z.proximal_body + 60.0,
                      now=datetime(2026, 8, 20, 13, 45, tzinfo=timezone.utc))
    assert plan.stop < z.distal, "stop must sit beyond the distal line"
    assert plan.risk_per_unit > 0 and plan.lots > 0, "sizing failed"
    assert plan.valid, f"plan unexpectedly rejected: {plan.notes}"

    tight = build_plan(z, atr[-1], equity=10_000, risk_pct=0.5,
                       liquidity_target=z.proximal_body + 1.0,
                       now=datetime(2026, 8, 20, 13, 45, tzinfo=timezone.utc))
    assert not tight.valid, "the 3R reward gate failed to reject a poor target"

    late = build_plan(z, atr[-1], equity=10_000, risk_pct=0.5,
                      htf_opposing=z.proximal_body + 60.0,
                      now=datetime(2026, 8, 20, 18, 30, tzinfo=timezone.utc))
    assert not late.valid, "the 17:00 UTC cutoff failed to reject a late entry"

    print("Self-test passed.")
    print(" zone :", z)
    print(" score:", {k: round(v, 1) for k, v in z.components.items()})
    print(" plan :", plan)
    return 0


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="al-Mizan li-l-Dhahab: XAUUSD supply/demand engine")
    ap.add_argument("--csv", help="M15 OHLC csv (time,open,high,low,close)")
    ap.add_argument("--h4", help="H4 OHLC csv, for bias")
    ap.add_argument("--d1", help="D1 OHLC csv, for bias")
    ap.add_argument("--equity", type=float, default=10_000.0)
    ap.add_argument("--risk", type=float, default=0.5, help="risk percent per trade")
    ap.add_argument("--all", action="store_true", help="print every graded zone, not just the selected two")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args(argv)

    if args.selftest or not args.csv:
        return _selftest()

    m15 = load_csv(args.csv)
    h4 = load_csv(args.h4) if args.h4 else None
    d1 = load_csv(args.d1) if args.d1 else None
    bias, zones, plans = analyse(m15, h4, d1, args.equity, args.risk)

    print(f"BIAS = {bias:+d}   candles = {len(m15)}   last = {m15[-1].c:.2f} @ {m15[-1].ts:%Y-%m-%d %H:%M}Z")
    if args.all:
        for z in sorted(zones, key=lambda x: -x.score):
            print("  ", z)
    print("-- selected --")
    for p in plans:
        print("  ", p.zone)
        print("  ", p)
    if not plans:
        print("   No zone balances. There is no 'almost'. Stand aside.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
