# AYA Line — #MoModel v4

> **First-principles institutional probability engine.**
> Built on BigBeluga's Volumatic z-score, layered with multi-test acceptance,
> persistence tracking, efficiency measurement, and mean-reversion gating.
> Outputs one number you can act on: **Continuation Probability**.

## The headline

```
ContProb  =  quality × efficiency × persistence × (1 − MR_factor)  × 100
```

Quality is itself a *geometric mean* of four normalised components — any
weak link drags the whole probability down. No additive scoring tricks.

## What this is NOT

✗ EMA crossovers · ✗ RSI · ✗ MACD · ✗ ATR-bias  
✗ Random S/R lines · ✗ Arbitrary RR multiples · ✗ Lagging oscillators

## What this IS

The seven market-maker questions, mapped to deterministic math:

| Q | Question                                  | Answered by                            |
|---|-------------------------------------------|----------------------------------------|
| 1 | Where was inventory acquired?             | Origin Zone (range, not a line)        |
| 2 | Was control transferred?                  | Pivot BOS **or** fast-impulse BOS      |
| 3 | Did the auction accept the price?         | 3 simultaneous tests (A · B · C)       |
| 4 | Is participation continuing?              | Persistence ratio                      |
| 5 | Is the trend efficient?                   | Net-move / total-path                  |
| 6 | Is mean reversion likely?                 | Distance in R units                    |
| 7 | Where is the next liquidity pool?         | BSL · SSL · PDH · PDL · FVG            |

## Files

| File                | Purpose                                                  |
|---------------------|----------------------------------------------------------|
| `AYA_Line.pine`     | Pine Script **v6** — the full v4 engine                  |
| `Volumatic_SR.pine` | Pine Script **v5** — BigBeluga's original (MPL-2.0)      |
| `ROADMAP.md`        | Full mathematical framework + v3 → v4 migration notes    |

## Quick start (TradingView)

1. Pine Editor → paste `AYA_Line.pine` → Save → "Add to chart".
2. Recommended timeframe: **5m** or **15m**.
3. Watch the dashboard's **CONTINUATION %** row — that's your decision number.
4. Optional: also load `Volumatic_SR.pine` on the same chart to cross-reference
   the BigBeluga visual against the AYA origin zones.

## What you see on the chart

- **Origin zones** — green for demand, red for supply; rebuilt for each accepted origin.
- **Active zone** — bordered in bias colour with a dashed midline.
- **MOLiNE midlines** — dotted blue across each stored origin.
- **Continuation badge** — "ContProb 67% · Q78 · Eff 71% · Pers 68%" on the active zone.
- **BSL / SSL** — dotted lines at equal-high / equal-low clusters.
- **PDH / PDL** — dashed lines.
- **FVG boxes** — translucent purple over fair-value-gap zones.
- **BOS triangles** at every structural break.
- **Origin Accepted flag** when all three tests pass.
- **Bar-coloured expansion candles** (bull green / bear orange).
- **Mean-reversion warning flash** when `MR_factor ≥ 0.85`.

See `ROADMAP.md` for the complete first-principles derivation.
