# AYA — Bomb Market (First-Principles Intraday Strategy)

**Main strategy:** [`bomb_market.pine`](bomb_market.pine) — Pine Script v5, limit-entry-only intraday liquidity provision.

No lagging-indicator crossovers, no SMC pattern folklore. The strategy is derived
from four measurable properties of intraday markets, and every parameter maps to
one of them.

## First principles

**1. Why limit orders make money at all.**
Every trade has an aggressor (market order, pays the spread) and a provider
(limit order, earns it). Aggressive flow is aggressive because it's *urgent* —
stop cascades, liquidations, hedging — and urgent flow systematically overshoots
fair value. The only durable intraday edge available without colocation is being
the counterparty to forced flow. So: **entries are resting limit orders only**,
placed where forced flow overshoots, never chasing.

**2. Fair value is volume-weighted.**
The intraday benchmark institutions actually execute against is session VWAP.
The script computes an anchored VWAP plus a **volume-weighted standard deviation
(σ)**, so "how stretched is price" is measured in units the market itself defines.
(On volume-less FX feeds it degrades gracefully to a TWAP.)

**3. Volatility clusters and scales.**
Fixed pip/point thresholds are meaningless across XAUUSD, EURUSD, and indices, or
across hours of the day. Every distance in this system — arm level, order
placement, stop, target — is expressed in σ, so it self-scales across symbols
and intraday timeframes with no re-tuning.

**4. Mean reversion is a regime, not a law.**
Fading extremes works when the price path is noise and dies when it's
information. The regime gate is **Kaufman's Efficiency Ratio**
(|net move| ÷ path length over N bars) — a direct signal-to-noise measurement.
Low ER → choppy auction → fade enabled. High ER → information arriving → stand
down. A **trend-day circuit breaker** additionally disables a side when price
*camps* beyond the bands for several consecutive bars, until VWAP is re-touched.

## The trade

```
price stretched > armσ (2.0) from VWAP, in a noise regime, in session
   → rest a LIMIT order deeper at fillσ (2.5), re-quoted every bar as VWAP/σ move
   → only an overshoot spike can fill it (you are the counterparty to the puke)
   → target: reversion to VWAP (trailing — fair value keeps moving)
   → stop:  frozen at (stopσ − fillσ) beyond entry  = 1.5σ risk by default
   → time stop after N bars (reversion has a half-life) · flat at end of session
```

Unfilled orders are cancel/replaced every bar while armed and cancelled the
moment the setup lapses. No market orders for entry, ever.

## Expectancy, honestly

Default geometry: risk 1.5σ, reward ≈ 2.5σ back to VWAP → ~1.7R per winner with
a **high win rate** — that is the mathematically coherent shape of a
mean-reversion edge. Marketing that promises 1:15–1:50 R:R on every trade is
selling the opposite of how liquidity provision pays. Expectancy per trade:

```
E = p·(reward) − (1−p)·(risk) − costs
```

Costs matter enormously at intraday frequency — backtest with your real
commission and spread (the script ships with 2 ticks of slippage on stop/market
exits) before believing anything.

## Suggested presets

| Input                | 1m   | 5m   | 15m  |
|----------------------|------|------|------|
| Warm-up bars         | 30   | 12   | 8    |
| ER lookback          | 40   | 30   | 20   |
| Arm band (σ)         | 2.0  | 2.0  | 1.8  |
| Fill placement (σ)   | 2.6  | 2.5  | 2.2  |
| Stop (σ)             | 4.0  | 4.0  | 3.5  |
| Max hold (bars)      | 60   | 40   | 24   |

Session defaults to 07:00–20:00 UTC (London + New York liquidity); positions and
orders are flattened outside it.

## Risk

Position size = `(equity × risk%) / (stop distance × point value)` — constant
fractional risk per trade, default **0.5%**.

## Repo layout

- `bomb_market.pine` — the strategy (v2, first-principles).
- `legacy/bomb_market_smc.pine` — the earlier SMC-style reconstruction
  (sweep → displacement → order-block limit, fixed 15–50R targets), kept for
  reference and comparison.
