"""Volume footprint reconstruction from OHLCV bars.

Pure-stdlib reference implementation of the model derived in docs/DERIVATION.md.

The whole construction rests on three assumptions:

  A1  price is continuous -- it visited every level between the extremes it touched
  A2  volume accrues in proportion to distance travelled (dV proportional to |dp|)
  A3  upward travel is buy-initiated, downward travel is sell-initiated

Everything below -- the bid/ask split, the per-level distribution, the delta,
the point of control -- is a consequence of those three and nothing else.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Iterable, Sequence

__all__ = [
    "Bar",
    "Leg",
    "FootprintConfig",
    "Row",
    "BarProfile",
    "decompose",
    "buy_share",
    "build_profile",
    "value_area",
    "overlap_coefficient",
    "SQRT2",
]

SQRT2 = math.sqrt(2.0)
_INV_SQRT_2PI = 1.0 / math.sqrt(2.0 * math.pi)

# Legs shorter than this fraction of the range contribute nothing meaningful and
# are dropped to keep the mixture tidy.
_EPS = 1e-12


# --------------------------------------------------------------------------- #
# Inputs
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class Bar:
    """One OHLCV bar.

    ``buy_volume`` is optional and only set when a genuine measurement exists
    (the ``ltf`` engine).  When present it overrides the modelled split for this
    bar, while the per-level *shape* still comes from the path decomposition.
    """

    o: float
    h: float
    l: float
    c: float
    v: float
    t: int = 0
    buy_volume: float | None = None

    def __post_init__(self) -> None:
        if not (self.l <= self.o <= self.h and self.l <= self.c <= self.h):
            raise ValueError(f"open/close outside high/low range: {self!r}")
        if self.v < 0:
            raise ValueError(f"negative volume: {self!r}")

    @property
    def range(self) -> float:
        return self.h - self.l

    @property
    def body(self) -> float:
        return self.c - self.o


@dataclass(frozen=True)
class Leg:
    """A monotone traversal of ``[lo, hi]`` carrying ``mass`` units of volume.

    By A2 the volume laid down per unit price is constant along a leg, so a leg
    is exactly a uniform density on ``[lo, hi]``.  ``up`` records the direction,
    which by A3 is the buy/sell label.
    """

    lo: float
    hi: float
    mass: float
    up: bool


@dataclass(frozen=True)
class FootprintConfig:
    row_size: float = 0.25
    """Height of one price row, in instrument price units (usually a tick multiple)."""

    concentration: float = 6.0
    """Kernel bandwidth as a divisor of the bar range: sigma = range / concentration.

    This is *not* the shape of the distribution -- the shape comes from the legs.
    It encodes how much we distrust the three-leg path approximation.  Large
    values sharpen towards the exact piecewise-uniform profile; ``inf`` disables
    smoothing entirely.

    Note this differs from models where a Gaussian *is* the assumed profile and
    needs a wide kernel (k ~ 3) to have any shape at all.  Here the legs already
    carry the shape, so the kernel only blurs; k ~ 6 is a sane default and small
    values wash out the very buy/sell asymmetry the model exists to express.
    """

    action_exponent: float = 1.0
    """Least-action exponent alpha weighting the two path hypotheses.

    0 = both paths equally likely, 1 = inverse-length (default), large = commit
    to the shorter path.
    """

    value_area_pct: float = 70.0
    imbalance_threshold: float = 3.0
    """Diagonal dominance ratio.  3.0 means one side must be 300% of the other."""

    balance_tilt_pct: float = 5.0
    """Below this |tilt| the bar is reported as balanced rather than directional."""

    engine: str = "path"
    """One of ``path``, ``close``, ``ltf``."""

    def sigma_for(self, rng: float) -> float:
        if self.concentration <= 0 or math.isinf(self.concentration):
            return 0.0
        return rng / self.concentration


# --------------------------------------------------------------------------- #
# Step 1-3: path decomposition and the bid/ask split
# --------------------------------------------------------------------------- #


def path_weights(bar: Bar, alpha: float = 1.0) -> tuple[float, float]:
    """Probability weights for the up-first and down-first path hypotheses.

    Path lengths collapse to ``len(A) = 2R + d`` and ``len(B) = 2R - d`` with
    ``R`` the range and ``d`` the body.  Weighting by ``len ** -alpha`` gives the
    least-action mix; at ``alpha = 1`` this is ``w_A = (2R - d) / 4R``.
    """
    r, d = bar.range, bar.body
    if r <= _EPS:
        return 0.5, 0.5
    len_a = 2.0 * r + d
    len_b = 2.0 * r - d
    if alpha == 0.0:
        return 0.5, 0.5
    # Both lengths are strictly positive whenever |d| <= R, guaranteed by A1.
    wa = len_a ** (-alpha)
    wb = len_b ** (-alpha)
    total = wa + wb
    return wa / total, wb / total


def decompose(bar: Bar, alpha: float = 1.0) -> list[Leg]:
    """Split a bar into weighted monotone legs.

    Path A (up first)   O -> H -> L -> C
    Path B (down first) O -> L -> H -> C

    Each path contributes three legs; the two paths are mixed by ``path_weights``.
    """
    o, h, l, c = bar.o, bar.h, bar.l, bar.c
    r = bar.range
    if r <= _EPS:
        # Degenerate bar: all volume at one price, split evenly.
        return [Leg(l, h, 0.5, True), Leg(l, h, 0.5, False)]

    wa, wb = path_weights(bar, alpha)
    legs = [
        # Path A: up O->H, down H->L, up L->C
        Leg(o, h, wa * (h - o), True),
        Leg(l, h, wa * r, False),
        Leg(l, c, wa * (c - l), True),
        # Path B: down O->L, up L->H, down H->C
        Leg(l, o, wb * (o - l), False),
        Leg(l, h, wb * r, True),
        Leg(c, h, wb * (h - c), False),
    ]
    return [leg for leg in legs if leg.mass > _EPS]


def buy_share(bar: Bar, cfg: FootprintConfig) -> float:
    """Fraction of the bar's volume that was buy-initiated.

    ``path``  -- ratio of up-leg mass to total leg mass (the derived model).
    ``close`` -- the naive ``(C - L) / (H - L)``.
    ``ltf``   -- the measured split carried on the bar, if any.
    """
    if cfg.engine == "ltf" and bar.buy_volume is not None:
        if bar.v <= 0:
            return 0.5
        return _clamp(bar.buy_volume / bar.v, 0.0, 1.0)

    if cfg.engine == "close":
        if bar.range <= _EPS:
            return 0.5
        return _clamp((bar.c - bar.l) / bar.range, 0.0, 1.0)

    legs = decompose(bar, cfg.action_exponent)
    up = sum(leg.mass for leg in legs if leg.up)
    total = sum(leg.mass for leg in legs)
    if total <= _EPS:
        return 0.5
    return up / total


# --------------------------------------------------------------------------- #
# Step 4: per-level distribution
# --------------------------------------------------------------------------- #


def _phi(z: float) -> float:
    """Standard normal density."""
    return _INV_SQRT_2PI * math.exp(-0.5 * z * z)


def _Phi(z: float) -> float:
    """Standard normal CDF."""
    return 0.5 * (1.0 + math.erf(z / SQRT2))


def _Psi(z: float) -> float:
    """Antiderivative of the normal CDF: Psi'(z) = Phi(z).

    Psi(z) = z*Phi(z) + phi(z), since phi'(z) = -z*phi(z) cancels the z*phi(z)
    term from differentiating the product.
    """
    return z * _Phi(z) + _phi(z)


def leg_mass_in_row(leg: Leg, p1: float, p2: float, sigma: float) -> float:
    """Mass a leg deposits into the price row ``[p1, p2]``.

    With ``sigma == 0`` this is plain interval overlap -- exact, since the leg is
    a uniform density.  With ``sigma > 0`` the uniform is convolved with a normal
    kernel first; the integral stays closed-form via ``Psi``.
    """
    a, b = leg.lo, leg.hi
    width = b - a

    if sigma <= 0.0:
        if width <= _EPS:
            return leg.mass if p1 <= a < p2 else 0.0
        overlap = min(p2, b) - max(p1, a)
        return leg.mass * max(0.0, overlap) / width

    if width <= _EPS:
        # Point mass smeared by the kernel.
        return leg.mass * (_Phi((p2 - a) / sigma) - _Phi((p1 - a) / sigma))

    acc = (
        _Psi((p2 - a) / sigma)
        - _Psi((p1 - a) / sigma)
        - _Psi((p2 - b) / sigma)
        + _Psi((p1 - b) / sigma)
    )
    return leg.mass * sigma * acc / width


def row_bounds(bar: Bar, row_size: float) -> tuple[int, int]:
    """Inclusive index range of tick-aligned rows touched by the bar.

    Rows are anchored to an absolute grid (row ``k`` spans ``[k*s, (k+1)*s)``)
    rather than to each bar's low, so that rows from different bars line up.
    Without that alignment, diagonal comparisons across bars are meaningless.
    """
    if row_size <= 0:
        raise ValueError("row_size must be positive")
    k_lo = math.floor(bar.l / row_size)
    k_hi = math.floor(bar.h / row_size)
    if k_hi < k_lo:
        k_hi = k_lo
    # A high sitting exactly on a boundary opens a row of zero width; drop it.
    if k_hi > k_lo and abs(bar.h - k_hi * row_size) <= _EPS:
        k_hi -= 1
    return k_lo, k_hi


# --------------------------------------------------------------------------- #
# Outputs
# --------------------------------------------------------------------------- #


@dataclass
class Row:
    index: int
    """Absolute grid index; ``price_low == index * row_size``."""
    price_low: float
    price_high: float
    buy: float = 0.0
    sell: float = 0.0

    @property
    def total(self) -> float:
        return self.buy + self.sell

    @property
    def delta(self) -> float:
        return self.buy - self.sell

    @property
    def mid(self) -> float:
        return 0.5 * (self.price_low + self.price_high)


@dataclass
class BarProfile:
    bar: Bar
    rows: list[Row]
    buy_volume: float
    sell_volume: float
    poc_index: int
    val_index: int
    vah_index: int
    buy_imbalances: list[int] = field(default_factory=list)
    sell_imbalances: list[int] = field(default_factory=list)
    ovl: float = 1.0

    # -- scalar read-outs ---------------------------------------------------- #

    @property
    def total_volume(self) -> float:
        return self.buy_volume + self.sell_volume

    @property
    def delta(self) -> float:
        return self.buy_volume - self.sell_volume

    @property
    def tilt_pct(self) -> float:
        """Delta as a percentage of total volume."""
        t = self.total_volume
        return 0.0 if t <= 0 else 100.0 * self.delta / t

    @property
    def residual_ppm(self) -> float:
        """Volume conservation error in parts per million (float noise only)."""
        if self.bar.v <= 0:
            return 0.0
        return abs(sum(r.total for r in self.rows) - self.bar.v) / self.bar.v * 1e6

    def row(self, index: int) -> Row | None:
        for r in self.rows:
            if r.index == index:
                return r
        return None

    @property
    def poc(self) -> Row:
        return self.rows[self.poc_index]

    def balance_label(self, threshold_pct: float = 5.0) -> str:
        tilt = self.tilt_pct
        if abs(tilt) < threshold_pct:
            return "balanced"
        return "buyers" if tilt > 0 else "sellers"

    def stacked_imbalances(self, min_run: int = 3) -> list[tuple[str, list[int]]]:
        """Runs of consecutive imbalanced rows on the same side.

        A single imbalance is noise; a stack of them is the classic absorption /
        initiative signature, which is why runs are reported rather than points.
        """
        out: list[tuple[str, list[int]]] = []
        for side, marks in (("buy", self.buy_imbalances), ("sell", self.sell_imbalances)):
            run: list[int] = []
            for idx in sorted(marks):
                if run and idx == run[-1] + 1:
                    run.append(idx)
                else:
                    if len(run) >= min_run:
                        out.append((side, run))
                    run = [idx]
            if len(run) >= min_run:
                out.append((side, run))
        return out


# --------------------------------------------------------------------------- #
# Assembly
# --------------------------------------------------------------------------- #


def build_profile(
    bar: Bar,
    cfg: FootprintConfig | None = None,
    sub_bars: Sequence[Bar] | None = None,
) -> BarProfile:
    """Reconstruct the footprint of a single bar.

    ``sub_bars`` drives the ``ltf`` engine: each sub-bar is decomposed on its own
    legs with its own split and the results are summed, so the model degrades
    gracefully into the truth as the sub-timeframe shrinks.
    """
    cfg = cfg or FootprintConfig()

    k_lo, k_hi = row_bounds(bar, cfg.row_size)
    rows = [
        Row(k, k * cfg.row_size, (k + 1) * cfg.row_size)
        for k in range(k_lo, k_hi + 1)
    ]
    index_of = {r.index: i for i, r in enumerate(rows)}

    if cfg.engine == "ltf" and sub_bars:
        for sub in sub_bars:
            _accumulate(sub, cfg, rows, index_of, share=buy_share(sub, cfg))
    else:
        _accumulate(bar, cfg, rows, index_of, share=buy_share(bar, cfg))

    # Renormalise so volume is conserved exactly.  Kernel smoothing leaks mass
    # past the bar extremes and the row grid is finite, so the raw sums are
    # slightly short; the target totals come from the chosen engine.
    share = buy_share(bar, cfg)
    if cfg.engine == "ltf" and sub_bars:
        sub_v = sum(s.v for s in sub_bars)
        if sub_v > 0:
            share = sum(buy_share(s, cfg) * s.v for s in sub_bars) / sub_v

    target_buy = bar.v * share
    target_sell = bar.v - target_buy
    _rescale(rows, target_buy, target_sell)

    poc_i = _argmax(rows)
    val_i, vah_i = value_area(rows, poc_i, cfg.value_area_pct)
    buy_imb, sell_imb = _imbalances(rows, cfg.imbalance_threshold)

    return BarProfile(
        bar=bar,
        rows=rows,
        buy_volume=sum(r.buy for r in rows),
        sell_volume=sum(r.sell for r in rows),
        poc_index=poc_i,
        val_index=val_i,
        vah_index=vah_i,
        buy_imbalances=buy_imb,
        sell_imbalances=sell_imb,
        ovl=overlap_coefficient(rows),
    )


def _accumulate(
    bar: Bar,
    cfg: FootprintConfig,
    rows: list[Row],
    index_of: dict[int, int],
    share: float,
) -> None:
    """Deposit one bar's leg mixture into the shared row grid."""
    legs = decompose(bar, cfg.action_exponent)
    if not legs:
        return
    sigma = cfg.sigma_for(bar.range)

    up_mass = sum(leg.mass for leg in legs if leg.up) or 1.0
    dn_mass = sum(leg.mass for leg in legs if not leg.up) or 1.0

    # Shape comes from the legs; totals come from the engine's split.  Under the
    # `path` engine these already agree and the scaling is the identity.
    buy_scale = bar.v * share / up_mass
    sell_scale = bar.v * (1.0 - share) / dn_mass

    for leg in legs:
        scale = buy_scale if leg.up else sell_scale
        for row in rows:
            m = leg_mass_in_row(leg, row.price_low, row.price_high, sigma)
            if m <= 0.0:
                continue
            if leg.up:
                row.buy += m * scale
            else:
                row.sell += m * scale


def _rescale(rows: list[Row], target_buy: float, target_sell: float) -> None:
    got_buy = sum(r.buy for r in rows)
    got_sell = sum(r.sell for r in rows)
    if got_buy > _EPS:
        k = target_buy / got_buy
        for r in rows:
            r.buy *= k
    elif rows:
        rows[_mid_index(rows)].buy = target_buy
    if got_sell > _EPS:
        k = target_sell / got_sell
        for r in rows:
            r.sell *= k
    elif rows:
        rows[_mid_index(rows)].sell = target_sell


def _mid_index(rows: list[Row]) -> int:
    return len(rows) // 2


def _argmax(rows: list[Row]) -> int:
    best, best_v = 0, -1.0
    for i, r in enumerate(rows):
        if r.total > best_v:
            best, best_v = i, r.total
    return best


def value_area(rows: Sequence[Row], poc_i: int, pct: float = 70.0) -> tuple[int, int]:
    """Smallest contiguous band around the POC holding ``pct`` of total volume.

    Grown greedily outward, annexing whichever neighbour carries more volume.
    The 70% convention is inherited from market profile, not derived -- it is
    roughly the +/-1 sigma mass of a normal.
    """
    if not rows:
        return 0, 0
    total = sum(r.total for r in rows)
    if total <= 0:
        return poc_i, poc_i
    target = total * pct / 100.0

    lo = hi = poc_i
    acc = rows[poc_i].total
    while acc < target and (lo > 0 or hi < len(rows) - 1):
        below = rows[lo - 1].total if lo > 0 else -1.0
        above = rows[hi + 1].total if hi < len(rows) - 1 else -1.0
        if above >= below:
            hi += 1
            acc += above
        else:
            lo -= 1
            acc += below
    return lo, hi


def _imbalances(rows: Sequence[Row], threshold: float) -> tuple[list[int], list[int]]:
    """Diagonal imbalances, compared across the spread rather than within a level.

    Buyers at row k traded against sellers resting one row below, so that is the
    comparison that carries information.
    """
    buys: list[int] = []
    sells: list[int] = []
    for i, row in enumerate(rows):
        if i > 0:
            ref = rows[i - 1].sell
            if row.buy > threshold * ref and row.buy > 0:
                buys.append(i)
        if i < len(rows) - 1:
            ref = rows[i + 1].buy
            if row.sell > threshold * ref and row.sell > 0:
                sells.append(i)
    return buys, sells


def overlap_coefficient(rows: Sequence[Row]) -> float:
    """Shared area of the normalised buy and sell profiles, in [0, 1].

    1.00 means both sides traded at identical prices (two-sided rotation); a low
    value means the sides were segregated by price, i.e. one side was chasing.
    A model that gives buy and sell the same shape pins this at 1.00 and so
    cannot express the distinction at all.
    """
    b_total = sum(r.buy for r in rows)
    s_total = sum(r.sell for r in rows)
    if b_total <= 0 or s_total <= 0:
        return 0.0
    return sum(min(r.buy / b_total, r.sell / s_total) for r in rows)


def _clamp(x: float, lo: float, hi: float) -> float:
    return lo if x < lo else hi if x > hi else x


# --------------------------------------------------------------------------- #
# Multi-bar aggregation
# --------------------------------------------------------------------------- #


def session_profile(
    profiles: Iterable[BarProfile], row_size: float
) -> tuple[list[Row], int, int, int]:
    """Merge bar profiles onto the shared grid: composite rows, POC, VAL, VAH.

    Row indices are absolute, so merging is a plain key-wise sum -- which is the
    payoff of anchoring the grid to price rather than to each bar's low.
    """
    merged: dict[int, Row] = {}
    for prof in profiles:
        for r in prof.rows:
            m = merged.get(r.index)
            if m is None:
                m = Row(r.index, r.price_low, r.price_high)
                merged[r.index] = m
            m.buy += r.buy
            m.sell += r.sell

    if not merged:
        return [], 0, 0, 0

    lo_k, hi_k = min(merged), max(merged)
    rows = [
        merged.get(k) or Row(k, k * row_size, (k + 1) * row_size)
        for k in range(lo_k, hi_k + 1)
    ]
    poc_i = _argmax(rows)
    val_i, vah_i = value_area(rows, poc_i)
    return rows, poc_i, val_i, vah_i
