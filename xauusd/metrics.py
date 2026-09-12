"""Performance metrics. R-multiples first, dollars second.

Dollars depend on the size of the account and the leverage of the broker.
R-multiples depend on the strategy. Judge the strategy.
"""

from __future__ import annotations

import math
from collections import Counter, defaultdict
from dataclasses import dataclass, field

from .broker import Trade, breakeven_win_rate


@dataclass(slots=True)
class Stats:
    trades: int = 0
    wins: int = 0
    losses: int = 0
    win_rate: float = 0.0
    breakeven_win_rate: float = 0.0
    edge_margin: float = 0.0        # win_rate - breakeven_win_rate
    expectancy_r: float = 0.0       # mean R per trade: the only number that matters
    total_r: float = 0.0
    profit_factor: float = 0.0
    net_pnl: float = 0.0
    return_pct: float = 0.0
    max_dd_pct: float = 0.0
    max_dd_r: float = 0.0
    max_consec_losses: int = 0
    avg_win_r: float = 0.0
    avg_loss_r: float = 0.0
    avg_bars_held: float = 0.0
    avg_mae_winners_r: float = 0.0  # how close winners came to stopping out
    avg_mfe_losers_r: float = 0.0   # how much losers gave back
    sharpe_per_trade: float = 0.0
    kelly_fraction: float = 0.0
    exit_reasons: dict[str, int] = field(default_factory=dict)
    monthly_r: dict[str, float] = field(default_factory=dict)
    long_trades: int = 0
    short_trades: int = 0
    long_expectancy_r: float = 0.0
    short_expectancy_r: float = 0.0


def compute(trades: list[Trade], start_equity: float, rr: float = 3.0) -> Stats:
    st = Stats(trades=len(trades))
    if not trades:
        return st

    rs = [t.r_multiple for t in trades]
    wins = [r for r in rs if r > 0]
    losses = [r for r in rs if r <= 0]
    st.wins, st.losses = len(wins), len(losses)
    st.win_rate = st.wins / st.trades
    st.total_r = sum(rs)
    st.expectancy_r = st.total_r / st.trades
    st.avg_win_r = sum(wins) / len(wins) if wins else 0.0
    st.avg_loss_r = sum(losses) / len(losses) if losses else 0.0

    # realised cost drag in R, measured rather than assumed
    cost_r = max(0.0, abs(st.avg_loss_r) - 1.0)
    st.breakeven_win_rate = breakeven_win_rate(rr, cost_r)
    st.edge_margin = st.win_rate - st.breakeven_win_rate

    gross_win = sum(t.pnl for t in trades if t.pnl > 0)
    gross_loss = -sum(t.pnl for t in trades if t.pnl <= 0)
    st.profit_factor = gross_win / gross_loss if gross_loss > 0 else float("inf")
    st.net_pnl = sum(t.pnl for t in trades)
    st.return_pct = st.net_pnl / start_equity * 100.0 if start_equity else 0.0

    st.max_dd_pct = _max_drawdown_pct(trades, start_equity)
    st.max_dd_r = _max_drawdown_r(rs)
    st.max_consec_losses = _max_consec_losses(rs)

    st.avg_bars_held = sum(t.bars_held for t in trades) / st.trades
    win_maes = [t.mae_r for t in trades if t.r_multiple > 0]
    loss_mfes = [t.mfe_r for t in trades if t.r_multiple <= 0]
    st.avg_mae_winners_r = sum(win_maes) / len(win_maes) if win_maes else 0.0
    st.avg_mfe_losers_r = sum(loss_mfes) / len(loss_mfes) if loss_mfes else 0.0

    if st.trades > 1:
        mean = st.expectancy_r
        var = sum((r - mean) ** 2 for r in rs) / (st.trades - 1)
        sd = math.sqrt(var)
        st.sharpe_per_trade = mean / sd if sd > 0 else 0.0
    st.kelly_fraction = _kelly(st.win_rate, st.avg_win_r, st.avg_loss_r)

    st.exit_reasons = dict(Counter(t.exit_reason for t in trades))
    monthly: dict[str, float] = defaultdict(float)
    for t in trades:
        if t.exit_ts:
            monthly[t.exit_ts.strftime("%Y-%m")] += t.r_multiple
    st.monthly_r = dict(sorted(monthly.items()))

    longs = [t.r_multiple for t in trades if t.side.sign > 0]
    shorts = [t.r_multiple for t in trades if t.side.sign < 0]
    st.long_trades, st.short_trades = len(longs), len(shorts)
    st.long_expectancy_r = sum(longs) / len(longs) if longs else 0.0
    st.short_expectancy_r = sum(shorts) / len(shorts) if shorts else 0.0
    return st


def _kelly(win_rate: float, avg_win_r: float, avg_loss_r: float) -> float:
    """Kelly fraction of the stop distance. Trade a quarter of it, at most:
    Kelly is optimal only if your estimates are exact, and they never are."""
    b = avg_win_r / abs(avg_loss_r) if avg_loss_r else 0.0
    if b <= 0:
        return 0.0
    f = (win_rate * (b + 1) - 1) / b
    return max(0.0, f)


def _max_drawdown_pct(trades: list[Trade], start_equity: float) -> float:
    peak = start_equity
    equity = start_equity
    worst = 0.0
    for t in trades:
        equity += t.pnl
        peak = max(peak, equity)
        if peak > 0:
            worst = max(worst, (peak - equity) / peak * 100.0)
    return worst


def _max_drawdown_r(rs: list[float]) -> float:
    peak = 0.0
    cum = 0.0
    worst = 0.0
    for r in rs:
        cum += r
        peak = max(peak, cum)
        worst = max(worst, peak - cum)
    return worst


def _max_consec_losses(rs: list[float]) -> int:
    worst = run = 0
    for r in rs:
        if r <= 0:
            run += 1
            worst = max(worst, run)
        else:
            run = 0
    return worst


def format_report(st: Stats, extra: dict[str, object] | None = None) -> str:
    """Human-readable report. Terse on purpose."""
    lines: list[str] = []
    add = lines.append
    add("=" * 66)
    add("  XAUUSD M5 | momentum displacement -> limit pullback | fixed 3:1")
    add("=" * 66)
    if extra:
        for k, v in extra.items():
            add(f"  {k:<28} {v}")
        add("-" * 66)
    add(f"  {'trades':<28} {st.trades}")
    add(f"  {'win rate':<28} {st.win_rate * 100:.2f}%")
    add(f"  {'break-even win rate':<28} {st.breakeven_win_rate * 100:.2f}%  (measured costs)")
    add(f"  {'EDGE MARGIN':<28} {st.edge_margin * 100:+.2f} pts")
    add(f"  {'expectancy':<28} {st.expectancy_r:+.4f} R / trade")
    add(f"  {'total':<28} {st.total_r:+.1f} R")
    add(f"  {'profit factor':<28} {st.profit_factor:.2f}")
    add(f"  {'avg win / avg loss':<28} {st.avg_win_r:+.2f} R / {st.avg_loss_r:+.2f} R")
    add(f"  {'net P&L':<28} {st.net_pnl:+,.2f} USD  ({st.return_pct:+.2f}%)")
    add(f"  {'max drawdown':<28} {st.max_dd_pct:.2f}%  ({st.max_dd_r:.1f} R)")
    add(f"  {'max consecutive losses':<28} {st.max_consec_losses}")
    add(f"  {'sharpe (per trade)':<28} {st.sharpe_per_trade:.3f}")
    add(f"  {'full kelly / suggested':<28} {st.kelly_fraction * 100:.2f}% / {st.kelly_fraction * 25:.2f}%")
    add(f"  {'avg bars held':<28} {st.avg_bars_held:.1f}  ({st.avg_bars_held * 5:.0f} min)")
    add(f"  {'winners MAE':<28} {st.avg_mae_winners_r:.2f} R  (stop room actually used)")
    add(f"  {'losers MFE':<28} {st.avg_mfe_losers_r:.2f} R  (given back)")
    add(f"  {'long / short':<28} {st.long_trades} @ {st.long_expectancy_r:+.3f} R"
        f"  |  {st.short_trades} @ {st.short_expectancy_r:+.3f} R")
    add(f"  {'exits':<28} {st.exit_reasons}")
    if st.monthly_r:
        add("-" * 66)
        add("  monthly R")
        keys = list(st.monthly_r)
        for row_start in range(0, len(keys), 4):
            chunk = keys[row_start : row_start + 4]
            add("   " + "  ".join(f"{k} {st.monthly_r[k]:+6.1f}" for k in chunk))
    add("=" * 66)
    return "\n".join(lines)
