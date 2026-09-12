"""XAUUSD M5 strategy: momentum displacement, then a limit order into the
pullback, fixed 3:1 reward:risk.

FIRST PRINCIPLES
----------------
At 3R gross you break even near a 27.5% win rate. So the only question worth
asking is: "can price plausibly travel 3R before it travels 1R?" Three things
make that true on gold's 5-minute chart, and nothing else does:

  1. VOLATILITY. 3R has to be reachable inside a few hours. R is sized from
     ATR, so the target scales with what the market is actually doing instead
     of some fixed pip number invented in 2009.
  2. DIRECTION. A 3R run needs a reason. We only trade with the H1 trend and
     only after a genuine displacement leg on M5 - price closing beyond the
     20-bar extreme. No displacement, no trade.
  3. ENTRY LOCATION. This is where 3R is won. Chasing the breakout puts the
     stop miles away and makes 3R a fantasy. So we never chase: a LIMIT order
     rests in the retracement, which buys a tight structural stop and turns
     the same move into 3R+.

THE ALGORITHM, APPLIED
----------------------
  - Question every requirement: no MACD, no stochastic, no "confluence" stack.
    Each filter must earn its place by changing the trade set.
  - Delete parts: one entry model, one exit, no trailing, no martingale, no
    grid, no averaging down. Fixed 3R or the stop. That is the entire exit.
  - Simplify: every level derives from ATR and the swing that created the leg.
  - Accelerate: unfilled orders die in an hour. Dead money is worse than a
    loss because it also costs you the next setup.
  - Automate: identical logic in Python (research) and MQL5 (live).
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .broker import Side
from .data import Bar
from .indicators import Series, atr, ema, rolling_max, rolling_min, rolling_percentile


@dataclass(slots=True)
class StrategyConfig:
    # --- reward:risk -------------------------------------------------------
    rr: float = 3.0                    # the ask: 3 to 1, fixed

    # --- displacement trigger ---------------------------------------------
    breakout_lookback: int = 20        # close beyond the extreme of N prior bars
    min_leg_atr: float = 1.0           # impulse leg must be >= this * ATR
    max_leg_atr: float = 6.0           # ... and not a parabolic blowoff

    # --- limit entry ------------------------------------------------------
    retrace: float = 0.382             # place the limit this deep into the leg
    use_ema_confluence: bool = True    # pull the limit to the EMA when deeper
    ema_pullback: int = 21

    # --- stop -------------------------------------------------------------
    sl_buffer_atr: float = 0.30        # beyond the leg origin, past the stop hunt
    min_r_atr: float = 0.50            # reject stops too tight to survive noise
    max_r_atr: float = 2.50            # reject stops so wide 3R can't be reached

    # --- regime filters ---------------------------------------------------
    ema_fast: int = 21
    ema_slow: int = 50
    htf_minutes: int = 60
    htf_ema: int = 21
    require_htf_bias: bool = True
    atr_period: int = 14
    atr_pct_window: int = 480          # ~2 trading days of M5 bars
    atr_pct_floor: float = 0.30        # dead tape cannot pay for 3R
    atr_pct_cap: float = 0.97          # nor can a news candle you got filled on

    # --- order lifecycle --------------------------------------------------
    expire_bars: int = 12              # 1 hour. Unfilled = stale = cancelled.
    invalidate_frac: float = 0.10      # cancel if close re-enters the leg origin

    # --- sessions (UTC minutes from midnight) -----------------------------
    # Gold trends during London and the NY overlap. Asia chops and eats 3R
    # setups for breakfast.
    sessions: tuple[tuple[int, int], ...] = ((7 * 60, 11 * 60), (12 * 60 + 30, 16 * 60 + 30))
    force_flat_minute: int = 20 * 60   # flat by 20:00 UTC, no thin-liquidity holds
    friday_cutoff_minute: int = 16 * 60  # no new risk into the weekend gap

    # --- risk -------------------------------------------------------------
    risk_pct: float = 0.005            # 0.5% of equity per trade
    max_trades_per_day: int = 4
    max_concurrent: int = 1
    daily_loss_stop_r: float = 2.0     # stop for the day after -2R realised
    move_sl_to_be_at_r: float = 0.0    # 0 = off. Pure 3:1, as specified.

    def validate(self) -> None:
        if self.rr <= 0:
            raise ValueError("rr must be positive")
        if not 0.0 < self.retrace < 1.0:
            raise ValueError("retrace must be in (0, 1)")
        if self.min_r_atr <= 0 or self.max_r_atr <= self.min_r_atr:
            raise ValueError("min_r_atr must be > 0 and < max_r_atr")
        if self.min_leg_atr <= 0 or self.max_leg_atr <= self.min_leg_atr:
            raise ValueError("leg bounds inconsistent")
        if self.expire_bars < 1:
            raise ValueError("expire_bars must be >= 1")
        if not 0.0 <= self.atr_pct_floor < self.atr_pct_cap <= 1.0:
            raise ValueError("atr percentile band inconsistent")
        for start, end in self.sessions:
            if not 0 <= start < end <= 24 * 60:
                raise ValueError(f"bad session window {(start, end)}")


@dataclass(slots=True)
class Setup:
    """A trade plan produced at the close of `signal_bar`, to rest as a limit
    order from the next bar onward."""

    side: Side
    entry: float
    sl: float
    tp: float
    r_price: float
    signal_bar: int
    expire_bar: int
    invalidate_close: float
    atr: float
    tag: str = ""


@dataclass(slots=True)
class Context:
    """Precomputed, index-aligned series. Built once per backtest."""

    bars: list[Bar]
    atr: Series
    atr_floor: Series
    atr_cap: Series
    ema_fast: Series
    ema_slow: Series
    ema_pull: Series
    prior_high: Series
    prior_low: Series
    leg_low: Series
    leg_high: Series
    htf_bias: list[int] = field(default_factory=list)
    minute_of_day: list[int] = field(default_factory=list)
    in_session: list[bool] = field(default_factory=list)


def build_context(bars: list[Bar], cfg: StrategyConfig) -> Context:
    """Precompute everything the signal needs, with no lookahead anywhere."""
    cfg.validate()
    closes = [b.close for b in bars]
    highs = [b.high for b in bars]
    lows = [b.low for b in bars]

    a = atr(bars, cfg.atr_period)
    ctx = Context(
        bars=bars,
        atr=a,
        atr_floor=rolling_percentile(a, cfg.atr_pct_window, cfg.atr_pct_floor),
        atr_cap=rolling_percentile(a, cfg.atr_pct_window, cfg.atr_pct_cap),
        ema_fast=ema(closes, cfg.ema_fast),
        ema_slow=ema(closes, cfg.ema_slow),
        ema_pull=ema(closes, cfg.ema_pullback),
        prior_high=rolling_max(highs, cfg.breakout_lookback, shift=1),
        prior_low=rolling_min(lows, cfg.breakout_lookback, shift=1),
        leg_low=rolling_min(lows, cfg.breakout_lookback + 1, shift=0),
        leg_high=rolling_max(highs, cfg.breakout_lookback + 1, shift=0),
    )
    ctx.htf_bias = _htf_bias(bars, cfg)
    ctx.minute_of_day = [b.ts.hour * 60 + b.ts.minute for b in bars]
    ctx.in_session = [
        any(start <= m < end for start, end in cfg.sessions) for m in ctx.minute_of_day
    ]
    return ctx


def _htf_bias(bars: list[Bar], cfg: StrategyConfig) -> list[int]:
    """+1 / -1 / 0 H1 trend bias, mapped to each M5 bar using only the last
    CLOSED H1 bar."""
    from .data import htf_index, resample

    htf = resample(bars, cfg.htf_minutes)
    htf_closes = [b.close for b in htf]
    htf_ema = ema(htf_closes, cfg.htf_ema)
    bias_htf: list[int] = []
    for i in range(len(htf)):
        e = htf_ema[i]
        e_prev = htf_ema[i - 1] if i > 0 else None
        if e is None or e_prev is None:
            bias_htf.append(0)
            continue
        if htf_closes[i] > e and e >= e_prev:
            bias_htf.append(1)
        elif htf_closes[i] < e and e <= e_prev:
            bias_htf.append(-1)
        else:
            bias_htf.append(0)
    idx = htf_index(bars, cfg.htf_minutes)
    return [bias_htf[j] if j >= 0 else 0 for j in idx]


def _tradeable(ctx: Context, i: int, cfg: StrategyConfig) -> bool:
    bar = ctx.bars[i]
    if not ctx.in_session[i]:
        return False
    if bar.ts.weekday() == 4 and ctx.minute_of_day[i] >= cfg.friday_cutoff_minute:
        return False
    a = ctx.atr[i]
    floor_, cap = ctx.atr_floor[i], ctx.atr_cap[i]
    if a is None or floor_ is None or cap is None:
        return False
    # Volatility band: too quiet and 3R is unreachable; too wild and the fill
    # you got was the last liquidity before the spike reverses.
    return floor_ <= a <= cap


def signal_at(ctx: Context, i: int, cfg: StrategyConfig) -> Setup | None:
    """Evaluate bar `i` at its close. Returns a plan to rest from bar i+1."""
    if i < max(cfg.breakout_lookback + 2, cfg.ema_slow + 2, cfg.atr_period + 2):
        return None
    if not _tradeable(ctx, i, cfg):
        return None

    bar = ctx.bars[i]
    a = ctx.atr[i]
    ef, es = ctx.ema_fast[i], ctx.ema_slow[i]
    if a is None or ef is None or es is None:
        return None

    long_ok = (
        ctx.prior_high[i] is not None
        and bar.close > ctx.prior_high[i]
        and ef > es
        and (not cfg.require_htf_bias or ctx.htf_bias[i] > 0)
    )
    short_ok = (
        ctx.prior_low[i] is not None
        and bar.close < ctx.prior_low[i]
        and ef < es
        and (not cfg.require_htf_bias or ctx.htf_bias[i] < 0)
    )
    if long_ok == short_ok:  # neither, or (impossibly) both
        return None

    side = Side.LONG if long_ok else Side.SHORT
    origin = ctx.leg_low[i] if long_ok else ctx.leg_high[i]
    if origin is None:
        return None
    leg = abs(bar.close - origin)
    if leg < cfg.min_leg_atr * a or leg > cfg.max_leg_atr * a:
        return None

    entry = _entry_price(ctx, i, side, origin, leg, cfg)
    sl = origin - cfg.sl_buffer_atr * a if long_ok else origin + cfg.sl_buffer_atr * a
    r_price = (entry - sl) if long_ok else (sl - entry)
    if r_price <= 0:
        return None
    # R must be big enough to survive noise but small enough that 3R is a
    # move gold actually makes in an hour or two.
    if not (cfg.min_r_atr * a <= r_price <= cfg.max_r_atr * a):
        return None

    tp = entry + cfg.rr * r_price if long_ok else entry - cfg.rr * r_price
    invalidate = (
        origin + cfg.invalidate_frac * leg if long_ok else origin - cfg.invalidate_frac * leg
    )
    return Setup(
        side=side,
        entry=round(entry, 3),
        sl=round(sl, 3),
        tp=round(tp, 3),
        r_price=r_price,
        signal_bar=i,
        expire_bar=i + cfg.expire_bars,
        invalidate_close=invalidate,
        atr=a,
        tag=f"{'L' if long_ok else 'S'}-brk{cfg.breakout_lookback}-r{cfg.retrace:g}",
    )


def _entry_price(
    ctx: Context, i: int, side: Side, origin: float, leg: float, cfg: StrategyConfig
) -> float:
    """Limit price inside the retracement.

    Base level is a fixed fraction of the impulse leg. When the pullback EMA
    sits deeper in the leg, use that instead: the tighter the entry, the
    smaller R, and the more reachable 3R becomes. Never place the limit beyond
    the leg origin - that is no longer a pullback, it is a failed breakout.
    """
    close = ctx.bars[i].close
    if side is Side.LONG:
        level = close - cfg.retrace * leg
        e = ctx.ema_pull[i]
        if cfg.use_ema_confluence and e is not None and origin < e < level:
            level = e
        return max(level, origin + 0.05 * leg)
    level = close + cfg.retrace * leg
    e = ctx.ema_pull[i]
    if cfg.use_ema_confluence and e is not None and level < e < origin:
        level = e
    return min(level, origin - 0.05 * leg)
