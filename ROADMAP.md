# AYA Line — Volume-Engine Roadmap & Logical Approach

> "Less is better. Precision over frequency. Protect capital first."
>
> — AYA Line core philosophy

This document is the engineering blueprint behind the **AYA Line — Volume Engine**
Pine Script v6 indicator (`AYA_Line.pine`). The model is **100 % volume-driven**:
no EMAs, no ATR, no daily pivots. Every gate uses one of five volume tools.

---

## 1. Mission Statement

AYA Line is a *decision-support* indicator that mechanizes an institutional
intraday operator's read of the order book through volume:

1. Establish a **volume bias** (the *AYA Arrow*) from the consensus of three
   orderflow signals.
2. Anchor the bias to a **single core level** (the *AYA Line*) sourced from
   volume — anchored session VWAP, volume POC, or manual.
3. Define an **invalidation** rule that only the 1H full-body close past a
   volume reference (VAL/VAH, nearest HVN, or POC) can break.
4. Project **R-multiple targets** (TP1 → TP2 → TP3, ≥ 1:4).
5. Highlight **supply / demand zones** + **HVN levels** as confluence pickups.
6. Print **risk notes**: what invalidates, what confirms, when *not* to trade.

---

## 2. Volume Inputs (the only inputs)

| # | Tool                                  | Role                                                                        |
|---|----------------------------------------|------------------------------------------------------------------------------|
| 1 | **Anchored Session VWAP** + ±1σ bands | Fair value anchor; slope = trend pressure                                    |
| 2 | **Volume Profile** (POC / VAH / VAL)  | Where price *transacted* — auction value area                                |
| 3 | **Cumulative Volume Delta**            | Orderflow proxy (signed volume); sign = aggressor                            |
| 4 | **HVN Levels** (BigBeluga z-score)    | High-volume nodes = sticky S/R                                               |
| 5 | **Supply / Demand zones**              | Last opposing bar before a volume impulse (z-scored body × volume)           |

---

## 3. Component Roadmap

### 3.1 Anchored Session VWAP

- Reset on each new session (D / W / M selectable).
- Online accumulator: `Σ(typ·vol) / Σvol`.
- Variance band: `σ = √(Σ(typ²·vol)/Σvol − VWAP²)`.
- ±1σ bands optionally drawn.

### 3.2 Volume Profile

- Rolling lookback (default 288 bars, 50 bins).
- Each bar's volume distributed evenly across the bins its `[low,high]`
  range covers.
- **POC** = bin with greatest accumulated volume.
- **VAH / VAL** = expanded from POC bin until 70 % of total volume is captured
  (greedy expansion on the side with more adjacent volume).
- Recomputed on `barstate.islast` to keep cost bounded.

### 3.3 Cumulative Volume Delta

- Three selectable proxies: body sign × volume, up-tick vs down-tick,
  above-mid vs below-mid.
- Resets on session boundary.
- CVD > 0 = net buying pressure; CVD < 0 = net selling.

### 3.4 HVN Levels (Volumatic z-score)

Direct port of BigBeluga's logic:
```
zVol  = z-score(signed-volume,  200)
zDiff = z-score(close-open,     200)
HVN_bull ⇔ zVol >  L  AND  zDiff >  L
HVN_bear ⇔ zVol < -L  AND  zDiff < -L
```
Each HVN is plotted as a horizontal line at the bar's `(open+close)/2`,
extended right. Newest *N* (default 8) are kept.

### 3.5 Supply / Demand Zones

A zone is born when an **impulse** prints (`|zVol| > 1.8` and `|zDiff| > 1.8`).
- **Demand**: last *down* bar immediately preceding a bullish impulse;
  zone = `[low, max(open, close)]`.
- **Supply**: last *up* bar immediately preceding a bearish impulse;
  zone = `[min(open, close), high]`.

Newest *N* (default 4 each side) drawn as translucent boxes.

### 3.6 Volume Bias Engine (the AYA Arrow)

Three orthogonal volume signals; need majority + lead:

| Signal               | Bullish  | Bearish |
|----------------------|----------|---------|
| aVWAP slope (20-bar) | up       | down    |
| CVD sign             | positive | negative|
| close vs POC         | above    | below   |

```
bullPts = #signals_for_bull
bearPts = #signals_for_bear
bias    =  1  if bullPts >= 2 and bullPts > bearPts
        = -1  if bearPts >= 2 and bearPts > bullPts
        =  0  otherwise
confidence = leader * 33  (0..99)
```

The bias only **flips on a new 1H bar** to avoid intra-hour noise.

### 3.7 AYA Line (anchor)

Selectable source: anchored session VWAP / volume POC / manual override.
Drawn as a thick gold line across all timeframes.

### 3.8 Invalidation

`invLevel` is volume-derived — picks one of:
- **VAL / VAH** (default) — auction value-area edge.
- **Nearest HVN** in the bias direction.
- **POC** — point of control.

A 1H candle invalidates *only* if:
```
|body| / |range|  ≥  bodyPct  (default 0.6)
AND  bias == BULL  →  close_1H  <  invLevel
OR   bias == BEAR  →  close_1H  >  invLevel
```
Wicks never invalidate.

### 3.9 Targets

`R = |AYA Line − invLevel|`

| Target | Formula                  | Notes                       |
|--------|--------------------------|-----------------------------|
| TP1    | `AYA + dir · 1.0 · R`    | first liquidity sweep       |
| TP2    | `AYA + dir · 2.0 · R`    | session expansion           |
| TP3    | `AYA + dir · 4.0 · R`    | minimum asymmetric (1:4)    |

Targets are cancelled on invalidation.

### 3.10 Dashboard

Top-right table mirrors the system schema:

```
┌──────────────────────────────────────────────┐
│ VOLUME BIAS     | BULLISH ▲  (66)            │
│ AYA LINE        | 23 415.50  src: aVWAP       │
│ POC / VAH / VAL | 23 410 / 23 462 / 23 350    │
│ CVD             | +12 304 504  ▲              │
│ INVALIDATION    | 23 350.00  ref: VAL/VAH     │
│ TP1 / TP2 / TP3 | 23 481 / 23 547 / 23 678    │
│ HVN LEVELS      | 6 active                    │
│ S/D ZONES       | demand 3   supply 2         │
│ DO-NOT-TRADE    | —                           │
│ PHILOSOPHY      | Volume only · ≥1:4 · 1H inv │
└──────────────────────────────────────────────┘
```

---

## 4. Build Order (script top-to-bottom)

1. `//@version=6` + `indicator()` declaration.
2. Inputs (9 groups, all volume).
3. Anchored Session VWAP + bands.
4. Volume Profile (rebuild on last bar).
5. CVD accumulator.
6. HVN z-score detector + level array.
7. Supply / Demand zone detector + box arrays.
8. AYA Line resolution.
9. Bias engine (consensus of three signals).
10. Invalidation engine (1H full-body close vs volume reference).
11. Target projection.
12. Drawing layer (lines, boxes, labels — rebuilt last bar).
13. Dashboard table.
14. Alert conditions.

---

## 5. Guardrails Encoded in the Script

| Guardrail                            | How                                                |
|--------------------------------------|-----------------------------------------------------|
| Wicks never invalidate               | Full-body % filter on 1H close                     |
| Single in-flight bias                | State machine `{BULL, BEAR, NEUTRAL}`              |
| Bias only flips on new 1H            | Gated by `ta.change(time("60"))`                   |
| Min 1:4 RR                           | `rrTP3 ≥ 1.0` enforced (default 4.0)               |
| Targets die on invalidation          | Cleared in drawing layer                           |
| Compressed / unbuilt = stand down    | "do-not-trade" row keys on aVWAP std-dev / VP NA   |

---

## 6. Roadmap Beyond v1

- v1.1 — multi-session volume profile (RTH vs ETH split).
- v1.2 — footprint-style delta divergence detector.
- v1.3 — webhook payload for execution bot.
- v1.4 — `strategy()` clone for back-testing same logic core.
- v2.0 — adaptive R-multiples based on realised-volume regime.

---

> "Capital preservation creates longevity. Longevity creates opportunity."

