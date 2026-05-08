# AYA Line — #MoModel Institutional Engine

> "Statistical Expansion + Institutional Participation  
>  + Auction Acceptance + Liquidity Targeting"

## What this is

An institutional-grade intraday decision-support indicator built on a single
mathematical foundation: **BigBeluga's Volumatic z-score**.

Nothing else is used as an entry filter. No EMAs, no RSI, no ATR-bias,
no arbitrary fibs. Only statistically abnormal order flow events that pass
three additional confirmation gates.

## Files

| File                | Purpose                                                                  |
|---------------------|--------------------------------------------------------------------------|
| `AYA_Line.pine`     | Pine Script **v6** — the full #MoModel pipeline                          |
| `Volumatic_SR.pine` | Pine Script **v5** — BigBeluga's original indicator (MPL-2.0)            |
| `ROADMAP.md`        | Full mathematical framework, design decisions, and build order           |

## The 6-Step Pipeline

```
Step 1 — Statistical Expansion   z_diff × z_vol (BigBeluga z-score)
Step 2 — Structure Shift (BOS)   close > prior pivot high / low
Step 3 — Acceptance Test         price holds above/below origin ≤ N bars
Step 4 — Momentum Quality Score  0–100 (expansion + volume + range rank)
Step 5 — Liquidity Targets       BSL/SSL equal H/L · PDH/PDL · FVG voids
Step 6 — Invalidation            full-body close back through origin
```

Only origins that pass ALL gates are drawn as **MOLiNE** (Bus Origin) levels.

## What it draws

- **MOLiNE** — active Bus Origin levels, colored by acceptance / invalidation.
- **Volume box** — BigBeluga-style volume annotation at the origin candle.
- **Quality badge** — score label (✓ valid / ✗ invalidated) on each MOLiNE.
- **BOS markers** — triangle on every structural break.
- **Origin Accepted** — flag when all gates pass.
- **BSL / SSL** — equal-high / equal-low liquidity pools.
- **PDH / PDL** — prior day high and low.
- **FVG boxes** — fair value gaps (unfilled price imbalances).
- **Dashboard** — 10-row table: state · origin · quality · z-scores · liquidity.

## Quick start (TradingView)

1. Open TradingView → Pine Editor.
2. Paste the contents of `AYA_Line.pine`.
3. Save → "Add to chart".
4. Recommended timeframe: **5m** or **15m**.

## Companion: Volumatic S/R Levels

`Volumatic_SR.pine` is BigBeluga's full standalone indicator. The z-score
logic inside it is the mathematical foundation of `AYA_Line.pine`. Run it
alongside to see the full BigBeluga visual (percent labels, volume boxes,
max/min table) as a cross-reference for the MOLiNE levels.

See `ROADMAP.md` for the complete mathematical specification.
