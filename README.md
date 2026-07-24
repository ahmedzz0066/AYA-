# AYA — Bomb Market Strategy (Reverse-Engineered)

A Pine Script v6 reconstruction of the premium **"Bomb Market"** strategy,
reverse-engineered from published trade screenshots (XAUUSD, EURUSD, GBPUSD,
USDJPY, GBPCHF · 1m → 1D).

**Core idea:** liquidity sweep at a swing extreme → explosive displacement
away from it ("the bomb") → mark a thin wick-to-body band at the origin →
trade the retest with a stop a few ticks beyond the wick, targeting large
R-multiples (the source material shows 1:7 → 1:50+).

## Files

- [`bomb_market.pine`](bomb_market.pine) — TradingView strategy (Pine v6):
  zone detection, resting-limit entries, risk-based sizing, trend filter,
  alerts, stats table.
- [`docs/BOMB_MARKET_ANALYSIS.md`](docs/BOMB_MARKET_ANALYSIS.md) — full
  reverse-engineering breakdown, screenshot-by-screenshot, plus an honest
  quant reality check on the advertised R/R figures.

## Usage

1. Open TradingView → Pine Editor → paste `bomb_market.pine` → *Add to chart*.
2. Start with defaults on 1H/4H FX or gold; tune **Displacement filter**,
   **Target (R multiple)** and **Zone thickness** per instrument.
3. Set realistic commission/slippage in *Properties* before trusting results.

> ⚠️ Research/educational code. The huge advertised risk-reward ratios rely
> on sub-spread stop distances — see the analysis doc before trading.
