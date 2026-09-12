"""Event-driven bar-by-bar backtester.

One bar at a time, decisions made at the close of bar i and acted on from bar
i+1. No vectorised shortcuts, because shortcuts are where lookahead hides.

Intrabar sequencing (pessimistic, in order):
  1. An open position is checked for stop BEFORE target. If a single bar
     touches both, the loss is booked. Gold's 5-minute bars are violent and
     you do not get to assume the nice one happened first.
  2. A resting limit that fills on the same bar that then hits its stop is
     recorded as filled and stopped. Worst case, always.
  3. Stops slip; targets do not.

Feed 1-minute bars to `refine` if you want the true sequence resolved instead
of assumed - but the assumption is a floor on reality, which is the useful
direction to be wrong in.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

from .broker import (
    Costs,
    Order,
    Side,
    Trade,
    commission,
    gross_pnl,
    limit_fills,
    size_lots,
    stop_fill_price,
    stop_hit,
    target_hit,
)
from .data import Bar
from .strategy import Context, Setup, StrategyConfig, build_context, signal_at


@dataclass(slots=True)
class BacktestResult:
    trades: list[Trade]
    equity_curve: list[tuple[object, float]]
    start_equity: float
    end_equity: float
    setups: int
    filled: int
    expired: int
    invalidated: int
    skipped_size: int
    bars: int

    @property
    def fill_rate(self) -> float:
        return self.filled / self.setups if self.setups else 0.0


@dataclass(slots=True)
class _DayState:
    day: date | None = None
    trades: int = 0
    realised_r: float = 0.0

    def roll(self, day: date) -> None:
        if day != self.day:
            self.day = day
            self.trades = 0
            self.realised_r = 0.0


def run(
    bars: list[Bar],
    cfg: StrategyConfig | None = None,
    costs: Costs | None = None,
    start_equity: float = 10_000.0,
    ctx: Context | None = None,
) -> BacktestResult:
    cfg = cfg or StrategyConfig()
    costs = costs or Costs()
    cfg.validate()
    ctx = ctx or build_context(bars, cfg)

    equity = start_equity
    trades: list[Trade] = []
    curve: list[tuple[object, float]] = []
    pending: list[Order] = []
    open_trades: list[Trade] = []
    day = _DayState()

    counters = {"setups": 0, "filled": 0, "expired": 0, "invalidated": 0, "skipped_size": 0}

    for i, bar in enumerate(bars):
        day.roll(bar.ts.date())

        # 1. manage open positions on this bar -----------------------------
        still_open: list[Trade] = []
        for tr in open_trades:
            closed = _manage(tr, bar, i, costs, cfg, ctx)
            if closed:
                equity += tr.pnl
                tr.equity_after = equity
                day.realised_r += tr.r_multiple
                trades.append(tr)
            else:
                still_open.append(tr)
        open_trades = still_open

        # 2. resting limit orders ------------------------------------------
        survivors: list[Order] = []
        for order in pending:
            if _order_dead(order, bar, i, cfg, ctx, counters):
                continue
            if len(open_trades) >= cfg.max_concurrent:
                survivors.append(order)      # keep resting, just cannot fill yet
                continue
            if not limit_fills(order, bar, costs):
                survivors.append(order)
                continue
            tr = Trade(
                side=order.side,
                lots=order.lots,
                entry_ts=bar.ts,
                entry_bar=i,
                entry=order.entry,
                sl=order.sl,
                tp=order.tp,
                r_price=order.r_price,
                tag=order.tag,
            )
            counters["filled"] += 1
            day.trades += 1
            # Pessimistic: a bar that fills us may also stop us out.
            if _manage(tr, bar, i, costs, cfg, ctx, just_filled=True):
                equity += tr.pnl
                tr.equity_after = equity
                day.realised_r += tr.r_multiple
                trades.append(tr)
            else:
                open_trades.append(tr)
        pending = survivors

        # 3. new signal at this close, resting from the next bar -----------
        setup = signal_at(ctx, i, cfg)
        if setup is not None:
            counters["setups"] += 1
            if _risk_allows(day, cfg, open_trades, pending):
                lots = size_lots(equity, cfg.risk_pct, setup.r_price, costs)
                if lots <= 0:
                    counters["skipped_size"] += 1
                else:
                    pending.append(_to_order(setup, lots))

        curve.append((bar.ts, equity + _open_equity(open_trades, bar, costs)))

    # anything still open at the end of the data is marked to market and closed
    last = bars[-1] if bars else None
    for tr in open_trades:
        if last is None:
            continue
        _close(tr, last, len(bars) - 1, last.close, "eod-data", costs)
        equity += tr.pnl
        tr.equity_after = equity
        trades.append(tr)

    return BacktestResult(
        trades=trades,
        equity_curve=curve,
        start_equity=start_equity,
        end_equity=equity,
        setups=counters["setups"],
        filled=counters["filled"],
        expired=counters["expired"],
        invalidated=counters["invalidated"],
        skipped_size=counters["skipped_size"],
        bars=len(bars),
    )


def _to_order(setup: Setup, lots: float) -> Order:
    return Order(
        side=setup.side,
        entry=setup.entry,
        sl=setup.sl,
        tp=setup.tp,
        lots=lots,
        submitted_bar=setup.signal_bar + 1,
        expire_bar=setup.expire_bar,
        invalidate_close=setup.invalidate_close,
        tag=setup.tag,
        r_price=setup.r_price,
    )


def _risk_allows(day: _DayState, cfg: StrategyConfig, open_trades: list[Trade], pending: list[Order]) -> bool:
    """Daily governor. Losing days are a fact of life; losing days that turn
    into blown accounts are a design defect."""
    if day.trades >= cfg.max_trades_per_day:
        return False
    if day.realised_r <= -abs(cfg.daily_loss_stop_r):
        return False
    if len(pending) >= cfg.max_concurrent + 1:
        return False
    return True


def _order_dead(
    order: Order, bar: Bar, i: int, cfg: StrategyConfig, ctx: Context, counters: dict[str, int]
) -> bool:
    """Cancel stale, invalidated, or out-of-session orders.

    Dead money is worse than a loss: it also blocks the next setup. Cycle time
    is a risk parameter.
    """
    if i > order.expire_bar:
        counters["expired"] += 1
        return True
    minute = ctx.minute_of_day[i]
    if minute >= cfg.force_flat_minute or not ctx.in_session[i]:
        counters["expired"] += 1
        return True
    prev_close = ctx.bars[i - 1].close if i > 0 else bar.open
    if order.side is Side.LONG and prev_close < order.invalidate_close:
        counters["invalidated"] += 1
        return True
    if order.side is Side.SHORT and prev_close > order.invalidate_close:
        counters["invalidated"] += 1
        return True
    return False


def _manage(
    tr: Trade,
    bar: Bar,
    i: int,
    costs: Costs,
    cfg: StrategyConfig,
    ctx: Context,
    just_filled: bool = False,
) -> bool:
    """Update excursions and close the trade if a level was hit. True = closed."""
    _update_excursions(tr, bar, costs)

    if stop_hit(tr.side, tr.sl, bar, costs):
        px = stop_fill_price(tr.side, tr.sl, bar, costs)
        reason = "be-stop" if tr.sl != tr.tp and tr.exit_reason == "" and _is_be(tr) else "stop"
        _close(tr, bar, i, px, reason, costs)
        return True

    if target_hit(tr.side, tr.tp, bar, costs):
        _close(tr, bar, i, tr.tp, "target", costs)
        return True

    # optional break-even move; off by default because the ask was a clean 3:1
    if cfg.move_sl_to_be_at_r > 0 and not _is_be(tr):
        trigger = tr.entry + tr.side.sign * cfg.move_sl_to_be_at_r * tr.r_price
        reached = bar.high >= trigger if tr.side is Side.LONG else bar.low <= trigger
        if reached:
            tr.sl = tr.entry

    if not just_filled and ctx.minute_of_day[i] >= cfg.force_flat_minute:
        _close(tr, bar, i, bar.close, "flat-time", costs)
        return True
    return False


def _is_be(tr: Trade) -> bool:
    return abs(tr.sl - tr.entry) < 1e-9


def _update_excursions(tr: Trade, bar: Bar, costs: Costs) -> None:
    if tr.r_price <= 0:
        return
    if tr.side is Side.LONG:
        adverse = (tr.entry - (bar.low - costs.half_spread)) / tr.r_price
        favourable = ((bar.high - costs.half_spread) - tr.entry) / tr.r_price
    else:
        adverse = ((bar.high + costs.half_spread) - tr.entry) / tr.r_price
        favourable = (tr.entry - (bar.low + costs.half_spread)) / tr.r_price
    tr.mae_r = max(tr.mae_r, adverse)
    tr.mfe_r = max(tr.mfe_r, favourable)


def _close(tr: Trade, bar: Bar, i: int, price: float, reason: str, costs: Costs) -> None:
    tr.exit = price
    tr.exit_bar = i
    tr.exit_ts = bar.ts
    tr.exit_reason = reason
    tr.pnl = gross_pnl(tr.side, tr.entry, price, tr.lots, costs) - commission(tr.lots, costs)
    risk_usd = tr.r_price * tr.lots * costs.contract_size
    tr.r_multiple = tr.pnl / risk_usd if risk_usd > 0 else 0.0


def _open_equity(open_trades: list[Trade], bar: Bar, costs: Costs) -> float:
    return sum(gross_pnl(t.side, t.entry, bar.close, t.lots, costs) for t in open_trades)
