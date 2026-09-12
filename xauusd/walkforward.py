"""Walk-forward optimisation.

An in-sample backtest is a story you tell yourself. The only question is
whether parameters chosen on the past survive on data they never saw. So:
train on a window, trade the next window blind, roll forward, and stitch the
out-of-sample trades together. That stitched curve is the only result worth
looking at.

Anti-curve-fitting rules baked in:
  - The parameter grid is small and every axis is economically meaningful.
  - Selection uses out-of-sample-free ranking on the training window only.
  - A fold that produces too few training trades selects the DEFAULTS rather
    than the best of a handful of lucky samples.
"""

from __future__ import annotations

import itertools
from dataclasses import dataclass, replace

from .backtest import run
from .broker import Costs, Trade
from .data import Bar
from .metrics import Stats, compute
from .strategy import Context, StrategyConfig, build_context

# Small on purpose. Each axis changes trade LOCATION or trade SELECTION, which
# is where an edge can actually live. Nobody ever found alpha in axis 14.
DEFAULT_GRID: dict[str, list[float | int]] = {
    "retrace": [0.236, 0.382, 0.5, 0.618],
    "sl_buffer_atr": [0.20, 0.30, 0.45],
    "breakout_lookback": [15, 20, 30],
    "expire_bars": [8, 12, 18],
}


@dataclass(slots=True)
class Fold:
    index: int
    train_start: int
    train_end: int
    test_start: int
    test_end: int
    chosen: dict[str, float | int]
    train_stats: Stats
    test_stats: Stats
    test_trades: list[Trade]


@dataclass(slots=True)
class WalkForwardResult:
    folds: list[Fold]
    oos_trades: list[Trade]
    oos_stats: Stats
    combos_tested: int

    @property
    def positive_folds(self) -> int:
        return sum(1 for f in self.folds if f.test_stats.expectancy_r > 0)


# Fields that change the precomputed indicator series. Two configs that agree
# on these can share one Context, which is most of the grid search's cost.
_CTX_FIELDS = (
    "atr_period", "atr_pct_window", "atr_pct_floor", "atr_pct_cap",
    "ema_fast", "ema_slow", "ema_pullback", "htf_minutes", "htf_ema",
    "breakout_lookback", "sessions",
)


class _ContextCache:
    """Build each distinct Context once per data slice. Delete the work, do
    not just make it faster."""

    def __init__(self, bars: list[Bar]) -> None:
        self._bars = bars
        self._cache: dict[tuple, Context] = {}

    def get(self, cfg: StrategyConfig) -> Context:
        key = tuple(getattr(cfg, f) for f in _CTX_FIELDS)
        ctx = self._cache.get(key)
        if ctx is None:
            ctx = build_context(self._bars, cfg)
            self._cache[key] = ctx
        return ctx

    @property
    def builds(self) -> int:
        return len(self._cache)


def score(st: Stats, min_trades: int) -> float:
    """Ranking function for the TRAINING window.

    Expectancy alone rewards a 4-trade fluke, so penalise thin samples and
    deep drawdowns. Nothing here is fitted; it is just a preference for
    robustness over a pretty number.
    """
    if st.trades < min_trades:
        return -1e9
    dd_penalty = 1.0 + st.max_dd_r / 10.0
    sample_weight = min(1.0, st.trades / (min_trades * 3.0))
    return st.expectancy_r * sample_weight / dd_penalty


def run_walkforward(
    bars: list[Bar],
    base: StrategyConfig | None = None,
    costs: Costs | None = None,
    train_bars: int = 16_000,   # ~2.5 months of M5
    test_bars: int = 4_000,     # ~3 weeks traded blind
    grid: dict[str, list[float | int]] | None = None,
    min_train_trades: int = 25,
    start_equity: float = 10_000.0,
    verbose: bool = True,
) -> WalkForwardResult:
    base = base or StrategyConfig()
    costs = costs or Costs()
    grid = grid or DEFAULT_GRID

    keys = list(grid)
    combos = [dict(zip(keys, values)) for values in itertools.product(*(grid[k] for k in keys))]

    folds: list[Fold] = []
    oos_trades: list[Trade] = []
    fold_idx = 0
    cursor = 0
    warmup = max(base.atr_pct_window, base.ema_slow * 4) + 50

    while cursor + train_bars + test_bars <= len(bars):
        train = bars[cursor : cursor + train_bars]
        # the test slice carries warmup bars so indicators are warm, but only
        # trades taken after the warmup boundary are counted as out-of-sample
        test_start = cursor + train_bars
        test = bars[test_start - warmup : test_start + test_bars]

        train_cache = _ContextCache(train)
        best_cfg: dict[str, float | int] = {}
        best_score = -1e18
        best_train: Stats | None = None
        for combo in combos:
            cfg = replace(base, **combo)
            res = run(train, cfg, costs, start_equity, ctx=train_cache.get(cfg))
            st = compute(res.trades, start_equity, cfg.rr)
            s = score(st, min_train_trades)
            if s > best_score:
                best_score, best_cfg, best_train = s, combo, st

        if best_score <= -1e8:  # nothing cleared the sample-size bar
            best_cfg = {k: getattr(base, k) for k in keys}
            best_train = best_train or Stats()

        cfg = replace(base, **best_cfg)
        res = run(test, cfg, costs, start_equity)
        kept = [t for t in res.trades if t.entry_bar >= warmup]
        st_test = compute(kept, start_equity, cfg.rr)

        folds.append(
            Fold(
                index=fold_idx,
                train_start=cursor,
                train_end=cursor + train_bars,
                test_start=test_start,
                test_end=test_start + test_bars,
                chosen=best_cfg,
                train_stats=best_train or Stats(),
                test_stats=st_test,
                test_trades=kept,
            )
        )
        oos_trades.extend(kept)
        if verbose:
            print(
                f"  fold {fold_idx:>2} | {bars[test_start].ts.date()} -> "
                f"{bars[min(test_start + test_bars - 1, len(bars) - 1)].ts.date()} | "
                f"{_fmt(best_cfg)} | OOS {st_test.trades:>3} trades "
                f"{st_test.expectancy_r:+.3f} R/trade  WR {st_test.win_rate * 100:.1f}%",
                flush=True,
            )
        cursor += test_bars
        fold_idx += 1

    return WalkForwardResult(
        folds=folds,
        oos_trades=oos_trades,
        oos_stats=compute(oos_trades, start_equity, base.rr),
        combos_tested=len(combos),
    )


def _fmt(combo: dict[str, float | int]) -> str:
    return " ".join(f"{k.split('_')[0]}={v:g}" for k, v in combo.items())


def parameter_stability(res: WalkForwardResult) -> dict[str, dict[str, int]]:
    """How often each value was chosen. A parameter that jumps around every
    fold is not a parameter, it is noise wearing a name tag."""
    out: dict[str, dict[str, int]] = {}
    for fold in res.folds:
        for k, v in fold.chosen.items():
            out.setdefault(k, {}).setdefault(f"{v:g}", 0)
            out[k][f"{v:g}"] += 1
    return out
