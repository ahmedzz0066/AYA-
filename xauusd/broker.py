"""Execution model: bid/ask, limit fills, stop/target triggering, sizing.

Design rule: every ambiguity resolves AGAINST us. If a bar could have hit the
stop or the target, it hit the stop. If a limit could have filled better than
its price on a gap, it filled at its price. A backtest that flatters you is
worse than no backtest, because it costs real money to discover the truth.

Bars carry MID prices. Live:
    ask = mid + spread/2      (you buy here)
    bid = mid - spread/2      (you sell here)
A long is opened at the ask and its SL/TP are triggered on the bid, which is
how MT5 actually behaves. That means the spread is paid inside the trigger
conditions rather than bolted on afterwards as a fudge factor.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from .data import Bar


class Side(Enum):
    LONG = 1
    SHORT = -1

    @property
    def sign(self) -> int:
        return self.value


@dataclass(slots=True, frozen=True)
class Costs:
    """All-in trading costs. Defaults are deliberately unkind."""

    spread: float = 0.30            # USD per oz, round-turn spread on XAUUSD M5
    commission_per_lot: float = 7.0  # USD per 1.0 lot, round turn
    stop_slippage: float = 0.10      # USD per oz of adverse slip on stop-outs
    contract_size: float = 100.0     # 1.00 lot = 100 oz, so $1 move = $100
    lot_step: float = 0.01
    min_lot: float = 0.01
    max_lot: float = 50.0

    @property
    def half_spread(self) -> float:
        return self.spread / 2.0


@dataclass(slots=True)
class Order:
    """A resting limit order."""

    side: Side
    entry: float          # limit price (ask level for longs, bid level for shorts)
    sl: float
    tp: float
    lots: float
    submitted_bar: int
    expire_bar: int       # inclusive: cancelled after this bar closes
    invalidate_close: float  # cancel if a close goes beyond this level
    tag: str = ""
    r_price: float = 0.0  # entry-to-stop distance in USD/oz


@dataclass(slots=True)
class Trade:
    side: Side
    lots: float
    entry_ts: datetime
    entry_bar: int
    entry: float
    sl: float
    tp: float
    r_price: float
    exit_ts: datetime | None = None
    exit_bar: int | None = None
    exit: float = 0.0
    exit_reason: str = ""
    pnl: float = 0.0          # net USD after commission
    r_multiple: float = 0.0   # net PnL expressed in units of initial risk
    mae_r: float = 0.0        # max adverse excursion, in R
    mfe_r: float = 0.0        # max favourable excursion, in R
    tag: str = ""
    equity_after: float = 0.0

    @property
    def bars_held(self) -> int:
        if self.exit_bar is None:
            return 0
        return self.exit_bar - self.entry_bar


def limit_fills(order: Order, bar: Bar, costs: Costs) -> bool:
    """Would this resting limit order fill inside `bar`?

    Long: the ASK must trade down to the limit -> mid_low + half_spread <= entry
    Short: the BID must trade up to the limit -> mid_high - half_spread >= entry
    """
    if order.side is Side.LONG:
        return bar.low + costs.half_spread <= order.entry
    return bar.high - costs.half_spread >= order.entry


def stop_hit(side: Side, sl: float, bar: Bar, costs: Costs) -> bool:
    """Long stops trigger on the bid, short stops on the ask."""
    if side is Side.LONG:
        return bar.low - costs.half_spread <= sl
    return bar.high + costs.half_spread >= sl


def target_hit(side: Side, tp: float, bar: Bar, costs: Costs) -> bool:
    if side is Side.LONG:
        return bar.high - costs.half_spread >= tp
    return bar.low + costs.half_spread <= tp


def stop_fill_price(side: Side, sl: float, bar: Bar, costs: Costs) -> float:
    """Stops slip. Gaps through the stop fill at the gap, not at the stop."""
    slip = costs.stop_slippage
    if side is Side.LONG:
        gapped = bar.open - costs.half_spread
        return min(sl - slip, gapped) if gapped < sl else sl - slip
    gapped = bar.open + costs.half_spread
    return max(sl + slip, gapped) if gapped > sl else sl + slip


def size_lots(equity: float, risk_pct: float, r_price: float, costs: Costs) -> float:
    """Fixed-fractional sizing rounded DOWN to the lot step.

    r_price is the entry-to-stop distance in USD/oz. Returns 0.0 when the
    smallest tradable lot would risk more than the budget - skipping a trade
    beats silently over-risking, which is how accounts die.
    """
    if r_price <= 0 or equity <= 0 or risk_pct <= 0:
        return 0.0
    risk_usd = equity * risk_pct
    raw = risk_usd / (r_price * costs.contract_size)
    lots = math.floor(raw / costs.lot_step) * costs.lot_step
    lots = round(lots, 8)
    if lots < costs.min_lot:
        return 0.0
    return min(lots, costs.max_lot)


def gross_pnl(side: Side, entry: float, exit_price: float, lots: float, costs: Costs) -> float:
    return side.sign * (exit_price - entry) * lots * costs.contract_size


def commission(lots: float, costs: Costs) -> float:
    return lots * costs.commission_per_lot


def breakeven_win_rate(rr: float, cost_in_r: float) -> float:
    """Win rate needed to break even at reward:risk `rr` with costs.

    p * (rr - c) = (1 - p) * (1 + c)  ->  p = (1 + c) / (1 + rr)
    At rr=3 and c=0.10R that is 27.5%. Everything this strategy does is in
    service of clearing that one number.
    """
    return (1.0 + cost_in_r) / (1.0 + rr)
