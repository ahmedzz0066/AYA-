# AYA — Bomb Market Strategy (Reverse-Engineered)

Pine Script v5 strategy: [`bomb_market.pine`](bomb_market.pine)

A reverse-engineered reconstruction of the "Bomb Market" class of premium
strategies — the ones marketed with 1:15 to 1:50+ risk-to-reward ratios on
XAUUSD, EURUSD, and equity indices across 15m / 1H / 4H / 1D.

## Where the massive R:R actually comes from

These systems don't predict better — they **enter tighter**. The R:R is a
product of entry mechanics, not signal quality:

1. **Liquidity sweep** — price wicks through a swing high/low (a stop hunt /
   raid on buy-side or sell-side liquidity) and closes back inside the range.
2. **Displacement** — within a few bars, an impulsive candle (body ≥ 1.2×ATR)
   drives away from the sweep, leaving a Fair Value Gap and breaking
   short-term structure (CHoCH).
3. **Limit entry at the origin extreme** — a resting **limit order** is placed
   at the extreme of the order block (the last opposite candle before the
   displacement). The stop hides a fraction of ATR beyond the sweep wick.

Because the entry sits at the zone extreme and the stop is just past the hunt
wick, the stop distance collapses to a handful of ticks/pips — so a fixed
target of 15R–50R is a *normal-looking* distance on the chart. That is the
entire trick.

**Entries are limit orders only.** No market orders. Unfilled orders are
cancelled after N bars, or immediately if price closes through the stop zone
or runs to target without a fill.

## Setup lifecycle (state machine)

```
IDLE ──sweep──▶ HUNT (N-bar window) ──displacement──▶ LIMIT RESTING
                     │ window expires                      │
                     ▼                                     ├─ filled  → bracket exit (SL / fixed-R TP)
                    IDLE                                   ├─ expired → cancel
                                                           └─ setup invalidated → cancel
```

## Suggested presets per timeframe

| Input                     | 15m  | 1H   | 4H   | 1D  |
|---------------------------|------|------|------|-----|
| Swing pivot length        | 5    | 5    | 4    | 3   |
| Sweep → displacement window | 8  | 6    | 5    | 4   |
| Min body (× ATR)          | 1.2  | 1.2  | 1.1  | 1.0 |
| Limit expiry (bars)       | 20   | 15   | 10   | 7   |
| Killzone filter           | ON   | ON   | OFF  | OFF |
| R:R target                | 15–25| 15–25| 25–50| 25–50|

Killzones default to London 07:00–10:00 and New York 13:30–16:00 (UTC) —
recommended ON for 15m/1H on FX and gold.

## Risk sizing

Position size = `(equity × risk%) / (stop distance × point value)`, so every
trade risks the same fraction of equity regardless of how tight the stop is.
Default risk is **0.5%** per trade.

## Honest caveats (what the sales page won't tell you)

- At 15R–50R targets the **win rate is structurally low** (often 5–15%).
  Profitability rests on a small number of full-target winners; expect long
  losing streaks and size accordingly.
- Backtests of ultra-high-R:R systems are extremely sensitive to spread,
  slippage on the stop, and whether the tight stop would have survived real
  tick data. Test with realistic commission/spread settings and bar
  magnifier before believing any equity curve.
- The stop-loss leg of the bracket is a protective stop order (standard for
  any bracket); the *entry* side is what's restricted to limit orders.

## Alerts

Every placed order fires an `alert()` with ticker, limit price, SL, TP, and
R:R — suitable for webhook/broker integration.
