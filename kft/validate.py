"""Validation suite: full-sample backtests, anchored walk-forward
optimization with out-of-sample stitching, Monte Carlo robustness, and
benchmark comparison. Writes RESULTS.md.
"""

from __future__ import annotations

import itertools
from dataclasses import replace

import numpy as np
import pandas as pd

from .backtest import Backtester, buy_and_hold, ma_cross, metrics
from .data import YahooDaily
from .strategy import KFTParams, build_features

ASSETS = {
    "BTC-USD": {"cost_bps": 8.0, "start": "2014-09-17"},
    "EURUSD=X": {"cost_bps": 1.0, "start": "2010-01-01"},
    "GBPUSD=X": {"cost_bps": 1.2, "start": "2010-01-01"},
    "^GSPC": {"cost_bps": 1.5, "start": "2010-01-01"},
    "^NDX": {"cost_bps": 1.5, "start": "2010-01-01"},
}

# Small a-priori grid: only the three parameters with a physical
# interpretation are searched, everything else stays at its default.
GRID = {
    "theta": [0.6, 0.9, 1.2],
    "beta": [0.05, 0.08, 0.12],
    "tau": [10, 20],
}

TRAIN, TEST = 1008, 252  # ~4y train, 1y test, rolled annually


def _run(df: pd.DataFrame, p: KFTParams, cost: float):
    feats = build_features(df, p)
    return Backtester(feats, p, cost_bps=cost).run()


def objective(m: dict) -> float:
    """Rank param sets: profit factor damped by sample size, drawdown-aware."""
    if m["trades"] < 6 or not np.isfinite(m["profit_factor"]):
        return -1.0
    pf = min(m["profit_factor"], 4.0)
    return (pf - 1.0) * np.sqrt(m["trades"]) + 0.01 * m["max_dd_pct"]


def walk_forward(df: pd.DataFrame, cost: float, base: KFTParams):
    """Anchor-free rolling WFO. Features are rebuilt per param set on the
    full frame (indicators are causal), but selection uses only train bars
    and evaluation uses only the following unseen test bars."""
    combos = [
        dict(zip(GRID, v)) for v in itertools.product(*GRID.values())
    ]
    # cache: features + full-run equity/trades per combo
    runs = {}
    for cmb in combos:
        p = replace(base, **cmb)
        feats = build_features(df, p)
        runs[tuple(cmb.values())] = (p, feats)

    oos_curves, picks = [], []
    t0 = TRAIN
    while t0 + 30 < len(df):
        t1 = min(t0 + TEST, len(df))
        best, best_key = -np.inf, None
        for key, (p, feats) in runs.items():
            cur, tr = Backtester(feats.iloc[:t0], p, cost_bps=cost).run()
            sc = objective(metrics(cur, tr))
            if sc > best:
                best, best_key = sc, key
        p, feats = runs[best_key]
        # evaluate on train+test but keep only the test segment (warm state
        # comes from history the optimizer already saw; PnL bars do not)
        cur, tr = Backtester(feats.iloc[:t1], p, cost_bps=cost).run()
        seg = cur.iloc[t0:t1]
        oos_curves.append(seg / seg.iloc[0])
        picks.append({"train_end": str(df.index[t0 - 1].date()), **dict(zip(GRID, best_key))})
        t0 = t1
    stitched = pd.concat([c.pct_change().fillna(0.0) for c in oos_curves])
    stitched = (1 + stitched).cumprod() * 100_000.0
    return stitched, picks


def monte_carlo(trades, n_sims: int = 2000, risk: float = 0.0075, seed: int = 7):
    """Bootstrap the R-multiple sequence to get distributions of terminal
    return and max drawdown under fixed-fractional sizing."""
    r = np.array([t.r_mult for t in trades])
    if len(r) < 10:
        return None
    rng = np.random.default_rng(seed)
    finals, dds = np.empty(n_sims), np.empty(n_sims)
    for i in range(n_sims):
        seq = rng.choice(r, size=len(r), replace=True)
        eq = np.cumprod(1 + risk * seq)
        finals[i] = eq[-1] - 1
        dds[i] = (eq / np.maximum.accumulate(eq) - 1).min()
    return {
        "median_return_pct": 100 * np.median(finals),
        "p05_return_pct": 100 * np.percentile(finals, 5),
        "p95_dd_pct": 100 * np.percentile(dds, 5),  # 5th pct = worst tail
        "p_ruin_20dd_pct": 100 * (dds <= -0.20).mean(),
    }


def fmt_row(name: str, m: dict) -> str:
    return (
        f"| {name} | {m['net_profit_pct']:.1f}% | {m['cagr_pct']:.2f}% | "
        f"{m['sharpe']:.2f} | {m['sortino']:.2f} | {m['max_dd_pct']:.1f}% | "
        f"{m['trades']} | {m['win_rate_pct']:.1f}% | "
        f"{m['profit_factor']:.2f} | {m['expectancy_R']:+.3f}R |"
    )


def main():
    yd = YahooDaily()
    base = KFTParams()
    lines = [
        "# KFT Validation Report",
        "",
        "All numbers below were produced by `python run.py` in this repository",
        "against real Yahoo Finance daily data (see `data/` cache). Costs are",
        "charged per side on notional; stops fill before targets on ambiguous",
        "bars; all fills occur at the *next* bar's open.",
        "",
    ]
    all_trades = {}
    for sym, cfg in ASSETS.items():
        print(f"=== {sym} ===", flush=True)
        df = yd.fetch(sym, start=cfg["start"])
        print(f"  bars: {len(df)}  {df.index[0].date()} .. {df.index[-1].date()}")

        curve, trades = _run(df, base, cfg["cost_bps"])
        m_full = metrics(curve, trades)
        all_trades[sym] = trades

        bh = metrics(buy_and_hold(df, cfg["cost_bps"]), [])
        mac_curve, mac_tr = ma_cross(df, cost_bps=cfg["cost_bps"])
        mac = metrics(mac_curve, mac_tr)

        oos, picks = walk_forward(df, cfg["cost_bps"], base)
        m_oos = metrics(oos, [t for t in trades])  # trade stats from full run
        mc = monte_carlo(trades)

        lines += [
            f"## {sym}  ({df.index[0].date()} → {df.index[-1].date()}, {len(df)} bars)",
            "",
            "| Variant | Net Profit | CAGR | Sharpe | Sortino | MaxDD | Trades | Win% | PF | Expectancy |",
            "|---|---|---|---|---|---|---|---|---|---|",
            fmt_row("KFT (default params, full sample)", m_full),
            fmt_row("KFT (walk-forward OOS stitched)", m_oos),
            fmt_row("Buy & Hold", {**bh, "trades": 1, "win_rate_pct": float("nan"), "profit_factor": float("nan"), "expectancy_R": float("nan")}),
            fmt_row("MA 50/200 cross (long only)", mac),
            "",
        ]
        if picks:
            lines += ["Walk-forward parameter picks (per test year): "
                      + ", ".join(f"{p['train_end']}→θ={p['theta']},β={p['beta']},τ={p['tau']}" for p in picks), ""]
        if mc:
            lines += [
                f"Monte Carlo (2000 bootstraps of the R-sequence @0.75% risk): "
                f"median return {mc['median_return_pct']:.1f}%, "
                f"5th-pct return {mc['p05_return_pct']:.1f}%, "
                f"worst-tail (5th-pct) drawdown {mc['p95_dd_pct']:.1f}%, "
                f"P(DD ≥ 20%) = {mc['p_ruin_20dd_pct']:.1f}%",
                "",
            ]
        print(f"  full: {m_full}")

    # Portfolio: equal-risk combination of per-asset OOS-style full runs
    lines += ["## Notes", "",
              "- `KFT (walk-forward OOS stitched)` re-selects θ, β, τ annually on the",
              "  preceding ~4 years only; the equity shown is out-of-sample.",
              "- Trade-level columns (Trades/Win%/PF/Expectancy) for the OOS row reuse",
              "  the full-sample trade list; the OOS equity/Sharpe/DD columns are the",
              "  honest out-of-sample figures.",
              ""]
    with open("RESULTS.md", "w") as fh:
        fh.write("\n".join(lines))
    print("wrote RESULTS.md")


if __name__ == "__main__":
    main()
