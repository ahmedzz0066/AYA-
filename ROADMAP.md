# AYA Line — #MoModel Institutional Engine  
## Roadmap & Mathematical Framework

> "Capital preservation creates longevity. Longevity creates opportunity."

---

## 0. Governing Principle

Before a single line is drawn, three questions are separated:

| Question                          | Answer in the model                         |
|-----------------------------------|---------------------------------------------|
| What is mathematically valid?     | Z-score of signed volume × price expansion  |
| What is statistically repeatable? | Acceptance of inventory by the auction      |
| What is only visual/chart noise?  | Everything else — dropped                   |

A market maker or liquidity engineer cares only about:

1. **Inventory** — where was it acquired?
2. **Liquidity** — where is the next pool?
3. **Imbalance** — did the auction accept the new price?
4. **Volatility expansion** — was the move statistically abnormal?
5. **Mean reversion probability** — has the origin been violated?

---

## 1. The Only Valid Input: BigBeluga Z-score

The BigBeluga Volumatic indicator provides the model's sole entry filter.

### Mathematical definition

```
diffPx    = close − open                         // price displacement
volSigned = close > open ? +volume : −volume     // signed volume

z_diff = (diffPx    − SMA(diffPx,    200)) / STDEV(diffPx,    200)
z_vol  = (volSigned − SMA(volSigned, 200)) / STDEV(volSigned, 200)

bullExpand ⇔  z_diff >  threshold  AND  z_vol >  threshold
bearExpand ⇔  z_diff < −threshold  AND  z_vol < −threshold
```

### Why this is valid

- Values |z| > 2.0 are statistically unusual (≈ 2.5 % of observations).
- True directional expansion requires **both** volatility expansion AND
  participation expansion simultaneously.
- This filter removes most random bars; only genuinely anomalous events pass.

### What z-score alone does NOT prove

High volume alone can be absorption, distribution, liquidation, hedging, or
continuation. **A line at a high-volume bar is not edge.** What matters is
how price behaves *after* the event. This is why three additional gates exist.

---

## 2. #MoModel Pipeline (6 Steps)

### Step 1 — Statistical Expansion (BigBeluga z-score)

Fires when `z_diff` and `z_vol` simultaneously exceed `threshold` in the same
direction. This marks a **Bus Origin Candidate**. No trade, no line yet.

### Step 2 — Structure Shift (Gate 1 — Break of Structure)

```
Bullish BOS ⇔  close  crosses above  last pivot high
Bearish BOS ⇔  close  crosses below  last pivot low
```

- Pivot = `ta.pivothigh / ta.pivotlow` with configurable lookback.
- Without this step there is **no proof of directional control**.
- The origin candidate is IDLE until BOS fires.

### Step 3 — Acceptance Test (Gate 2)

Within a configurable window (default 5 bars) after BOS:

```
Bull accepted ⇔  close  >  originPx  (price holds above origin midpoint)
Bear accepted ⇔  close  <  originPx  (price holds below origin midpoint)
```

If the window expires without acceptance: origin is reset (auction failed).

**This is the institutional secret.** Did the market *accept* higher/lower
prices? If yes, inventory was acquired and held. If no, the move was a
sweep or a false auction.

### Step 4 — Momentum Quality Score (0 – 100)

Computed at the moment of expansion (not at validation). Ranks the move:

| Component            | Max pts | Condition                                  |
|----------------------|---------|--------------------------------------------|
| Price z-score rank   | 25      | `|z_diff| ≥ threshold × 1.5`              |
| Volume z-score rank  | 25      | `|z_vol|  ≥ threshold × 1.5`              |
| Volume ratio (×SMA)  | 25      | `volume / SMA(volume,200) ≥ 3.0`          |
| Range ratio (×ATR)   | 25      | `(high−low) / ATR(200) ≥ 2.5`             |

Origins below `qualMin` (default 40) are detected but not stored.

### Step 5 — Liquidity Targets

Targets are **NOT** arbitrary RR multiples. They are liquidity pools:

| Level              | Definition                                              |
|--------------------|---------------------------------------------------------|
| **BSL**            | Cluster of equal swing highs (buy-side liquidity)       |
| **SSL**            | Cluster of equal swing lows (sell-side liquidity)       |
| **PDH / PDL**      | Prior day high / low (most watched session extremes)    |
| **Bull FVG**       | `high[2] < low` — unfilled upward imbalance             |
| **Bear FVG**       | `low[2]  > high` — unfilled downward imbalance          |

### Step 6 — Invalidation

```
Full-body bar ⇔  |close − open| / (high − low)  ≥  bodyRatio  (default 0.5)

Bull invalidated ⇔  close  <  originPx  on a full-body bar
Bear invalidated ⇔  close  >  originPx  on a full-body bar
```

Close back through the origin = inventory was distributed. Thesis dead.
Exit. Reassess from scratch.

---

## 3. What Is Removed (and Why)

| Removed                    | Reason                                              |
|----------------------------|-----------------------------------------------------|
| EMA crossovers             | Lagging; explain nothing about inventory            |
| RSI / MACD                 | Momentum oscillators measure effect, not cause      |
| ATR-based bias             | Volatility alone has no directional meaning         |
| Daily pivots / fibs        | Arbitrary; not derived from order flow              |
| Random S/R line extension  | High volume alone ≠ edge (absorption vs. expansion) |
| RR multiples as targets    | Institutions target liquidity, not geometry         |

---

## 4. Dashboard Schema

```
┌──────────────────────────────────────────────────────┐
│ ORIGIN STATE   │ VALID — BULL ▲                       │
│ BUS ORIGIN     │ 23 415.50                            │
│ QUALITY SCORE  │ HIGH  (78 / 100)                     │
│ zDiff / zVol   │ 2.91  /  3.12                        │
│ BSL / SSL      │ 23 498.00  /  23 312.00              │
│ PRIOR DAY H/L  │ 23 510.00  /  23 280.00              │
│ FVG ZONES      │ 2 active                             │
│ ORIGINS STORED │ 3 / 10                               │
│ DO-NOT-TRADE   │ —                                    │
│ FRAMEWORK      │ z-score + BOS + Acceptance + Liquidity│
└──────────────────────────────────────────────────────┘
```

---

## 5. Files

| File                | Purpose                                               |
|---------------------|-------------------------------------------------------|
| `AYA_Line.pine`     | Pine Script v6 — full #MoModel engine                 |
| `Volumatic_SR.pine` | Pine Script v5 — BigBeluga original (companion)       |
| `ROADMAP.md`        | This document                                         |

---

## 6. Roadmap Beyond v1

- v1.1 — multi-origin tracking (queue, not just latest candidate).
- v1.2 — footprint delta proxy using tick-rule CVD for finer acceptance.
- v1.3 — webhook payload for execution bot integration.
- v1.4 — `strategy()` clone to back-test pipeline over historical data.
- v2.0 — dynamic quality threshold adapting to volatility regime.
