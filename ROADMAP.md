# AYA Line — #MoModel v4
## First-Principles Probability Engine

> "Capital preservation creates longevity. Longevity creates opportunity."

---

## 0. The First-Principles Reset

Strip away all conventional trading-indicator thinking. Ask only:

1. **What is mathematically valid?**
   → Z-scored deviations from mean (statistically anomalous events).
2. **What is statistically repeatable?**
   → Multi-test acceptance gates filtering out single-bar coincidences.
3. **What is only chart noise?**
   → Pretty lines, lagging oscillators, arbitrary RR multiples.

A market maker / liquidity engineer thinks in **inventory, liquidity,
imbalance, volatility expansion, and mean reversion probability** — not in
"support/resistance lines that look pretty on the chart".

---

## 1. The Seven Market-Maker Questions

Every line of code in `AYA_Line.pine` answers exactly one of:

| #  | Question                                  | Answer in the model                     |
|----|-------------------------------------------|------------------------------------------|
| Q1 | Where was inventory acquired?             | **Origin Zone** (a *range*, not a line)  |
| Q2 | Was control transferred to the new side?  | **Structure Shift** (pivot OR fast)      |
| Q3 | Did the auction accept the new price?     | **3 simultaneous tests**                 |
| Q4 | Is participation continuing?              | **Persistence** (vol-conf / vol-total)   |
| Q5 | Is the move efficient?                    | **Efficiency** (net-move / total-path)   |
| Q6 | Is mean reversion likely?                 | **MR Factor** (distance in R units)      |
| Q7 | Where is the next liquidity pool?         | **Target Stack** (BSL/SSL/PDH/PDL/FVG)   |

---

## 2. The Headline Output

A single number — **Continuation Probability (ContProb)** — replaces every
binary signal.

```
ContProb  =  quality × efficiency × persistence × (1 − MR_factor)  × 100
```

All four factors are normalised to the [0, 1] range before multiplication.
The product is bounded in [0, 100]. **Multiplication, not addition** — any
factor near zero collapses the whole probability.

This is the only number you actually need to act on.

---

## 3. Detailed Pipeline

### 3.1 Z-score Engine (Step 1)

Direct port of BigBeluga's Volumatic z-score:

```
z_diff = (close − open  − SMA200(diff))      / STDEV200(diff)
z_vol  = (signedVol     − SMA200(signedVol)) / STDEV200(signedVol)

bullExpand ⇔  z_diff >  zLevel  AND  z_vol >  zLevel
bearExpand ⇔  z_diff < −zLevel  AND  z_vol < −zLevel
```

This is the *only* signal-generation primitive. Everything else is a filter.

### 3.2 Origin Zone — a *range*, not a point (Step 2)

Three modes:

| Mode                     | Bull zone                            | Bear zone                            |
|--------------------------|--------------------------------------|--------------------------------------|
| **Half-candle** (default)| `[low, (open+close)/2]`              | `[(open+close)/2, high]`             |
| Full-candle              | `[low, high]`                        | `[low, high]`                        |
| Anchored consolidation   | `[low_N, high_N]` of N prior bars    | same                                 |

**`R = top − bot`** — the inventory range. Used as the unit of distance for
mean-reversion calculations.

### 3.3 Structure Shift — multi-method BOS (Step 3)

Two methods, OR'd together:

- **Method A (slow / reliable)** — classical pivot break:
  `close crosses above last ta.pivothigh` (bull) — or `below last ta.pivotlow`
  (bear).
- **Method B (fast / aggressive)** — the impulse bar itself:
  `bullExpand AND close > highest(high[1], fastLen)` — or symmetric for bear.

Method B reduces lag dramatically when the impulse is decisive.

### 3.4 Acceptance — three simultaneous tests (Step 4)

Within the acceptance window (default 5 bars after BOS), all three must pass:

| Test | What it asks                                | Formula                                |
|------|---------------------------------------------|----------------------------------------|
| A    | Did price actually escape the zone?         | bull: `close > zoneTop`                |
| B    | Is volume in confirming direction?          | `volConf / volTotal ≥ accMinPer (0.55)`|
| C    | Is the trend efficient (clean, not chop)?   | `|net| / pathTotal ≥ accMinEff (0.40)` |

Failing any one = candidate is dropped at end of window.

### 3.5 Quality — multiplicative score (Step 5)

```
q1 = saturate(|z_diff|        / (zLevel × 1.5),  0, 1)   // expansion strength
q2 = saturate(|z_vol|         / (zLevel × 1.5),  0, 1)   // participation
q3 = saturate(volume / SMA200, 0, 3) / 3                 // volume ratio
q4 = saturate(range  / ATR200, 0, 2.5) / 2.5             // range ratio

quality_norm  =  ⁴√(q1 · q2 · q3 · q4)        // geometric mean
quality_pct   =  quality_norm × 100
```

The geometric mean punishes *any* weak component. A single q-value of 0.1
caps the whole score around 50, no matter how perfect the other three are.

### 3.6 Mean-Reversion Factor (Step 6)

```
distR    = |close − originMid| / R
MR_factor = clip( (distR − 1) / (mrMaxR − 1) ,  0, 1)
```

- At distance = 1 R: MR_factor ≈ 0 (no penalty)
- At distance = mrMaxR (default 3 R): MR_factor = 1 (full mean-reversion penalty)

When MR_factor ≥ 0.85, the chart background flashes orange and the dashboard
prints "extended — mean-reversion risk".

### 3.7 Liquidity Targets (Step 7)

Targets are **liquidity pools**, not arbitrary RR multiples:

| Pool       | Definition                                                |
|------------|-----------------------------------------------------------|
| **BSL**    | Cluster of equal swing highs (buy-side liquidity)         |
| **SSL**    | Cluster of equal swing lows (sell-side liquidity)         |
| **PDH/PDL**| Prior day session high / low                              |
| **Bull FVG**| `high[2] < low` — unfilled upward imbalance              |
| **Bear FVG**| `low[2]  > high` — unfilled downward imbalance           |

Equal-H/L scanning uses positive-step descending-index iteration to honour
Pine's loop-step constraint while still finding the *most-recent* cluster.

### 3.8 Invalidation (Step 8)

A **full-body** close back through the chosen reference:

```
fullBody  ⇔  |close − open| / (high − low)  ≥  invBody  (default 0.5)
```

Reference is selectable:
- **Outer edge** (default): worst inventory price (zoneBot for bull, zoneTop for bear)
- Inner edge: zone top for bull, zone bottom for bear (more conservative)
- Origin midpoint: zoneMid

Wicks never invalidate.

---

## 4. Dashboard Schema

```
┌──────────────────────────────────────────────────────┐
│ ORIGIN STATE      │ VALID — BULL ▲                    │
│ CONTINUATION %    │ 67%                               │   ← headline
│ QUALITY (geomean) │ 78 / 100                          │
│ ZONE  bot → top   │ 23 410.00  →  23 425.50           │
│ ACCEPT  A / B / C │ ✓   ✓   ✓                         │
│ EFF / PERS / MR   │ 71%  /  68%  /  18%               │
│ zDiff / zVol      │ 2.91  /  3.12                     │
│ BSL / SSL         │ 23 498.00  /  23 312.00           │
│ PDH / PDL         │ 23 510.00  /  23 280.00           │
│ FVG / ORIGINS     │ 2 fvg / 3 stored                  │
│ DO-NOT-TRADE      │ —                                 │
│ FRAMEWORK         │ z + BOS + Accept(A/B/C) + Liquidity → P │
└──────────────────────────────────────────────────────┘
```

All seven values feed off the same state machine; consistency is guaranteed.

---

## 5. What's New vs v3

| Aspect                  | v3                              | v4                                       |
|-------------------------|---------------------------------|------------------------------------------|
| Origin                  | Single price (midpoint)         | **Zone (range)** — 3 selectable modes    |
| Acceptance              | One test (close beyond level)   | **3 simultaneous tests** (A · B · C)     |
| Quality                 | Additive sum (q1 + q2 + q3 + q4)| **Geometric mean** — multiplicative      |
| BOS                     | Pivot break only                | Pivot **OR** fast (impulse-bar)          |
| Mean reversion          | None                            | **Continuous MR_factor** + alert         |
| Persistence             | None                            | **Tracked every bar after BOS**          |
| Efficiency              | None                            | **Tracked every bar after BOS**          |
| Headline output         | Pass/Fail                       | **Continuation Probability (0-100%)**    |
| Invalidation reference  | Single (origin midpoint)        | Selectable (outer / inner / mid)         |
| Dashboard rows          | 10                              | 12 (with full diagnostic breakdown)      |

---

## 6. Files

| File                | Purpose                                                   |
|---------------------|-----------------------------------------------------------|
| `AYA_Line.pine`     | Pine Script v6 — full v4 first-principles engine          |
| `Volumatic_SR.pine` | Pine Script v5 — BigBeluga's original (companion overlay) |
| `ROADMAP.md`        | This document                                             |

---

## 7. Roadmap Beyond v4

- v4.1 — adaptive z-threshold based on rolling realised volatility regime.
- v4.2 — re-test detection (price returns to zone, bounces) → quality boost.
- v4.3 — naked-POC tracking with rolling volume profile.
- v4.4 — Bayesian probability calibration from historical hit-rates.
- v4.5 — webhook payload for execution bot integration.
- v5.0 — `strategy()` clone for back-testing the same logic core.

---

> "The edge is not predicting. The edge is identifying where inventory was
> acquired, whether the auction accepted it, and where liquidity exists next."
