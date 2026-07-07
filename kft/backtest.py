"""Event-driven backtester for the KFT signal engine.

Execution model (deliberately conservative):
  * signals form on the close of bar t, fills happen at the open of t+1
  * stops/targets are evaluated intrabar against H/L; when both are touched
    in one bar the STOP is assumed to fill first
  * gaps through a level fill at the open, not at the level
  * costs are charged per side on traded notional
  * notional is capped at `max_lev` times equity
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from .strategy import KFTParams


@dataclass
class Trade:
    entry_date: object
    exit_date: object
    direction: int
    entry: float
    exit: float
    size: float
    r_mult: float
    pnl: float
    bars: int
    reason: str


class Backtester:
    def __init__(
        self,
        features: pd.DataFrame,
        params: KFTParams,
        cost_bps: float = 2.0,
        start_equity: float = 100_000.0,
        max_lev: float = 10.0,
    ):
        self.f = features
        self.p = params
        self.cost = cost_bps / 1e4
        self.e0 = start_equity
        self.max_lev = max_lev

    def run(self) -> tuple[pd.Series, list[Trade]]:
        f, p = self.f, self.p
        O = f["Open"].to_numpy(float)
        H = f["High"].to_numpy(float)
        L = f["Low"].to_numpy(float)
        Cl = f["Close"].to_numpy(float)
        atr_ = f["atr"].to_numpy(float)
        score = f["score"].to_numpy(float)
        phase = f["phase"].to_numpy(float)
        long_sig = f["long_sig"].to_numpy(bool)
        short_sig = f["short_sig"].to_numpy(bool)
        stop_mult = f["stop_mult"].to_numpy(float)
        n = len(f)

        equity = self.e0
        curve = np.full(n, np.nan)
        trades: list[Trade] = []

        pos = 0          # -1, 0, +1
        entry = stop = target = size = stop_dist = 0.0
        entry_i = 0
        hi_water = lo_water = 0.0
        reached_1r = False
        pending_exit = None   # reason string -> exit at next open
        pending_entry = 0     # -1/0/+1  -> enter at next open

        warm = 300  # feature warm-up
        for t in range(n):
            px_close = Cl[t]

            # ---- fills queued from bar t-1 happen at today's open ----
            if pos != 0 and pending_exit is not None:
                px = O[t]
                equity += self._close_pos(trades, f.index[t], pos, entry, px,
                                          size, stop_dist, t - entry_i,
                                          pending_exit)
                pos, pending_exit = 0, None
            if pos == 0 and pending_entry != 0 and t >= warm:
                d = pending_entry
                entry = O[t]
                sd = stop_dist  # fixed on signal bar
                if np.isfinite(entry) and sd > 0:
                    size = (p.risk * equity) / sd
                    size = min(size, self.max_lev * equity / entry)
                    stop = entry - d * sd
                    target = entry + d * p.r_target * sd
                    equity -= size * entry * self.cost
                    pos, entry_i = d, t
                    hi_water, lo_water = entry, entry
                    reached_1r = False
                pending_entry = 0

            # ---- manage open position on bar t ----
            if pos != 0:
                hi_water = max(hi_water, H[t])
                lo_water = min(lo_water, L[t])
                exited = False
                if pos > 0:
                    if O[t] <= stop:
                        equity += self._close_pos(trades, f.index[t], pos, entry,
                                                  O[t], size, stop_dist,
                                                  t - entry_i, "gap_stop")
                        pos, exited = 0, True
                    elif L[t] <= stop:
                        equity += self._close_pos(trades, f.index[t], pos, entry,
                                                  stop, size, stop_dist,
                                                  t - entry_i, "stop")
                        pos, exited = 0, True
                    elif H[t] >= target:
                        px = max(O[t], target) if O[t] >= target else target
                        equity += self._close_pos(trades, f.index[t], pos, entry,
                                                  px, size, stop_dist,
                                                  t - entry_i, "target")
                        pos, exited = 0, True
                else:
                    if O[t] >= stop:
                        equity += self._close_pos(trades, f.index[t], pos, entry,
                                                  O[t], size, stop_dist,
                                                  t - entry_i, "gap_stop")
                        pos, exited = 0, True
                    elif H[t] >= stop:
                        equity += self._close_pos(trades, f.index[t], pos, entry,
                                                  stop, size, stop_dist,
                                                  t - entry_i, "stop")
                        pos, exited = 0, True
                    elif L[t] <= target:
                        px = min(O[t], target) if O[t] <= target else target
                        equity += self._close_pos(trades, f.index[t], pos, entry,
                                                  px, size, stop_dist,
                                                  t - entry_i, "target")
                        pos, exited = 0, True

                if not exited and pos != 0:
                    # trailing engages after +1R excursion
                    if pos > 0 and hi_water >= entry + stop_dist:
                        reached_1r = True
                        stop = max(stop, Cl[t] - p.trail_atr * atr_[t])
                    elif pos < 0 and lo_water <= entry - stop_dist:
                        reached_1r = True
                        stop = min(stop, Cl[t] + p.trail_atr * atr_[t])
                    # decision exits -> queued to next open
                    unreal_r = pos * (px_close - entry) / stop_dist
                    if (t - entry_i) >= p.time_stop and unreal_r < 0.5:
                        pending_exit = "time"
                    elif phase[t] == -1 and not reached_1r:
                        pending_exit = "turbulence"
                    elif pos * score[t] <= -0.5 * p.theta:
                        pending_exit = "flip"

            # ---- new signals form on the close of bar t ----
            if pos == 0 and pending_entry == 0 and t >= warm:
                if long_sig[t]:
                    pending_entry = 1
                    stop_dist = stop_mult[t] * atr_[t]
                elif short_sig[t]:
                    pending_entry = -1
                    stop_dist = stop_mult[t] * atr_[t]

            # ---- mark to market ----
            mtm = equity
            if pos != 0:
                mtm += pos * size * (px_close - entry)
            curve[t] = mtm

        return pd.Series(curve, index=self.f.index, name="equity"), trades

    def _close_pos(self, trades, date, pos, entry, px, size, stop_dist,
                   bars, reason) -> float:
        gross = pos * size * (px - entry)
        cost = size * px * self.cost
        pnl = gross - cost
        trades.append(
            Trade(None, date, pos, entry, px, size,
                  pos * (px - entry) / stop_dist, pnl, bars, reason)
        )
        return pnl


# ----------------------------------------------------------------------
# Metrics & benchmarks
# ----------------------------------------------------------------------
def metrics(curve: pd.Series, trades: list[Trade], ppy: int = 252) -> dict:
    curve = curve.dropna()
    ret = curve.pct_change().dropna()
    yrs = len(curve) / ppy
    total = curve.iloc[-1] / curve.iloc[0] - 1.0
    cagr = (curve.iloc[-1] / curve.iloc[0]) ** (1 / max(yrs, 1e-9)) - 1.0
    sharpe = ret.mean() / (ret.std() + 1e-12) * np.sqrt(ppy)
    downside = ret[ret < 0].std()
    sortino = ret.mean() / (downside + 1e-12) * np.sqrt(ppy)
    dd = (curve / curve.cummax() - 1.0).min()
    r = np.array([t.r_mult for t in trades])
    pnl = np.array([t.pnl for t in trades])
    wins, losses = pnl[pnl > 0], pnl[pnl <= 0]
    pf = wins.sum() / (abs(losses.sum()) + 1e-12) if len(losses) else np.inf
    return {
        "net_profit_pct": 100 * total,
        "cagr_pct": 100 * cagr,
        "sharpe": sharpe,
        "sortino": sortino,
        "max_dd_pct": 100 * dd,
        "trades": len(trades),
        "win_rate_pct": 100 * (pnl > 0).mean() if len(pnl) else np.nan,
        "profit_factor": pf,
        "expectancy_R": r.mean() if len(r) else np.nan,
        "avg_bars": np.mean([t.bars for t in trades]) if trades else np.nan,
    }


def buy_and_hold(df: pd.DataFrame, cost_bps: float = 2.0) -> pd.Series:
    ret = df["Close"].pct_change().fillna(0.0)
    curve = (1 + ret).cumprod() * 100_000.0
    curve.iloc[-1] *= 1 - 2 * cost_bps / 1e4
    return curve.rename("equity")


def ma_cross(df: pd.DataFrame, fast: int = 50, slow: int = 200,
             cost_bps: float = 2.0) -> tuple[pd.Series, list[Trade]]:
    c = df["Close"]
    pos = (c.rolling(fast).mean() > c.rolling(slow).mean()).astype(float).shift(1).fillna(0.0)
    ret = c.pct_change().fillna(0.0) * pos
    flips = pos.diff().abs().fillna(0.0)
    ret -= flips * cost_bps / 1e4
    curve = (1 + ret).cumprod() * 100_000.0
    # synthesize trade records for win-rate style stats
    trades: list[Trade] = []
    in_pos, e_px, e_i = False, 0.0, 0
    for i in range(1, len(pos)):
        if pos.iloc[i] > 0 and not in_pos:
            in_pos, e_px, e_i = True, c.iloc[i], i
        elif pos.iloc[i] == 0 and in_pos:
            in_pos = False
            trades.append(Trade(None, c.index[i], 1, e_px, c.iloc[i], 1.0,
                                np.nan, c.iloc[i] - e_px, i - e_i, "cross"))
    return curve.rename("equity"), trades
