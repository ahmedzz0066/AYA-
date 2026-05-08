# AYA Line — Trading Model Roadmap & Logical Approach

> "Less is better. Precision over frequency. Protect capital first."
>
> — AYA Line core philosophy

This document is the engineering blueprint behind the **AYA Line** Pine Script v6
indicator (`AYA_Line.pine`). It translates the institutional-style intraday
framework into deterministic, chartable logic so every component on the chart can
be reasoned about, audited, and back-tested.

---

## 1. Mission Statement

AYA Line is **not** a signal generator. It is a *decision-support* indicator that
mechanizes the discretionary process of an institutional intraday operator:

1. Establish a **directional bias** at the start of the session (the *AYA Arrow*).
2. Anchor the bias to a **single core level** (the *AYA Line*).
3. Define an **invalidation** rule that only the 1H full-body close can break.
4. Project **probabilistic targets** (TP1 → TP2 → TP3 → Extended).
5. Highlight **pullback / pickup zones** that satisfy the asymmetric (≥1:4 RR)
   trade philosophy.
6. Read **market state** (trending / rotational / weak momentum) and surface it.
7. Print **risk notes**: what invalidates, what confirms, when *not* to trade.

Everything below is what the script must compute, in the order it computes it.

---

## 2. Timeframe Stack

| TF       | Role                                  | Used for                                              |
|----------|---------------------------------------|--------------------------------------------------------|
| Daily    | Macro bias anchor                     | Prior day OHLC, ATR(D), session pivots                 |
| 1H       | Directional control / invalidation    | **Only TF** allowed to invalidate the AYA Line         |
| 15m      | Structural read                       | BOS / CHOCH, premium-discount legs, liquidity pools    |
| 5m       | Execution refinement                  | Entry triggers, sweep + reclaim, micro MSS             |

The script subscribes to all four via `request.security` and renders on the
chart's current TF (recommended 5m or 15m).

---

## 3. Component Roadmap

### 3.1 Daily Directional Bias (AYA Arrow)

**Inputs**
- Prior day OHLC.
- Daily pivot `P = (PH + PL + PC) / 3`.
- 1H EMA(20) and EMA(50) (bias filter).
- Reclaim of prior day high / low.

**Decision tree**
```
if   close_1H > P  AND ema20_1H > ema50_1H AND close_1H > prevDayHigh_-1
        → bias = BULLISH    (confidence: HIGH)
elif close_1H > P  AND ema20_1H > ema50_1H
        → bias = BULLISH    (confidence: MEDIUM)
elif close_1H < P  AND ema20_1H < ema50_1H AND close_1H < prevDayLow_-1
        → bias = BEARISH    (confidence: HIGH)
elif close_1H < P  AND ema20_1H < ema50_1H
        → bias = BEARISH    (confidence: MEDIUM)
else
        → bias = NEUTRAL    (do not engage)
```
Confidence drives table colour and a numeric score (0–100).

### 3.2 Core AYA Line

The single level the entire session is built around. Selectable input:

1. **Daily pivot P** (default).
2. **Anchored VWAP** from session open.
3. **Prior day midpoint** `(PH + PL) / 2`.
4. **Manual override** (price input).

Drawn as a thick, persistent horizontal line on all timeframes.

### 3.3 Invalidation Level

- **Bullish bias** → invalidation = lowest 1H low over last `N=12` hours
  (configurable). Drawn as a dashed line.
- **Bearish bias** → invalidation = highest 1H high over last `N=12` hours.

**Invalidation rule (the only one that matters):**
```
A 1H candle is invalidating ⇔
    bias == BULL AND  close_1H  <  inv_level  AND  body_size >= 0.6 * range
                                                  (i.e. full-body, not a wick)
or
    bias == BEAR AND  close_1H  >  inv_level  AND  body_size >= 0.6 * range
```
Wicks alone never invalidate. The script paints the candle red and prints
`INVALIDATED` on the dashboard; signals are suppressed until a new bias forms.

### 3.4 Model Targets

Targets are projected from the AYA Line using a hybrid of **ATR(D)** expansion
and **R-multiples** measured against the invalidation distance `R`:

| Target | Formula (bullish; flip sign for bearish)                |
|--------|----------------------------------------------------------|
| TP1    | `AYA + 1.0 × R`           (≈ first liquidity sweep)       |
| TP2    | `AYA + 2.0 × R`           (session expansion)             |
| TP3    | `AYA + 4.0 × R`           (minimum asymmetric objective)  |
| Ext    | `AYA + max(6×R, 1.0×ATRd)` (momentum continuation)        |

`R = |AYA − invalidation|`. If a target lies the wrong side of the prior-day
range, it is faded but still drawn so traders can see liquidity context.

Targets are **cancelled** the moment the bias is invalidated; they reappear only
after a confirmed reclaim (see 3.7).

### 3.5 Pullback / Entry Zones

A discount zone (for longs) and premium zone (for shorts) are computed from the
last completed 15m impulse leg:

- **Leg** = swing low → swing high (or vice versa) over `pivotLen = 5`.
- **Discount** = 50 %–79 % retrace (Fibonacci): `[leg_high − 0.79·leg, leg_high − 0.5·leg]`.
- **Premium** = mirror of the above for shorts.
- **Sweet spot** = 70.5 % (OTE) — drawn as a dotted mid-line.

Boxes are extended right until price either tags them (entry candidate) or the
leg is invalidated by a structure shift.

### 3.6 Liquidity & Structure Reads

For each chart bar the script tracks:

- **BSL pools** (clusters of equal/buy-side highs).
- **SSL pools** (equal/sell-side lows).
- **Sweep events**: wick breaches an SSL/BSL pool but candle closes back inside.
- **MSS / BOS** on 5m and 15m via swing-pivot break.
- **Reclaims**: close back through the AYA Line in the bias direction after a
  prior break.

These feed into the *confirmation triggers* on the dashboard.

### 3.7 Reclaim & Reversal Logic

If invalidation fires the model becomes defensive. A new bias is **only**
allowed when *all* of the following occur in sequence on ≤ 15m:

1. Liquidity sweep beyond the prior invalidation level.
2. MSS in the new direction (close beyond opposing swing).
3. Reclaim of the AYA Line (or new pivot).
4. Momentum confirmation: 5m close in new direction with body ≥ 0.6 × range.

Until these happen the dashboard shows `DEFENSIVE — STAND DOWN`.

### 3.8 Market State Classification

Computed each bar from ATR ratios + structure:

| State            | Detection                                                                |
|------------------|---------------------------------------------------------------------------|
| **Trending**     | `ATR(14) > 1.2 × ATR(50)` AND consecutive HH/HL (or LH/LL) on 15m         |
| **Rotational**   | Price oscillating inside prior day range, ATR ratio ≈ 1                  |
| **Weak momentum**| `ATR(14) < 0.8 × ATR(50)` — script suggests reducing or skipping         |

### 3.9 Risk-Reward Visualisation

When price is inside the active pullback zone, the script draws a translucent
**risk box** (entry → invalidation) and a **reward box** (entry → TP3). The two
boxes are sized so the reader instantly verifies the ≥ 1:4 RR rule — if the
geometry can't satisfy it, the box is hatched and a warning printed.

### 3.10 Dashboard / Output Format

A top-right table mirrors the system's required output schema:

```
┌─────────────────────────────────────────────┐
│ DAILY BIAS    | BULLISH (HIGH 78)           │
│ AYA LINE      | 23 415.50                   │
│ INVALIDATION  | 23 312.20                   │
│ TP1 / TP2     | 23 518 / 23 622             │
│ TP3 / EXT     | 23 829 / 24 010             │
│ STATE         | TRENDING                    │
│ TRIGGER       | sweep + 5m MSS + reclaim    │
│ DO-NOT-TRADE  | weak momentum / news        │
└─────────────────────────────────────────────┘
```

Each row maps 1:1 to the user-facing system prompt sections
(`[ DAILY BIAS ]`, `[ CORE AYA LINE ]`, `[ MODEL TARGETS ]`,
`[ TRADE PLAN ]`, `[ MARKET STATE ]`, `[ RISK NOTES ]`).

---

## 4. Build Order (what the .pine file does, top-to-bottom)

1. `//@version=6` + `indicator()` declaration with `overlay=true`,
   `max_lines_count=500`, `max_boxes_count=500`, `max_labels_count=500`.
2. Inputs (groups): *Bias*, *AYA Line*, *Invalidation*, *Targets*,
   *Pullback*, *Liquidity*, *Style*, *Dashboard*.
3. HTF data fetch via `request.security` (D, 60, 15).
4. Core calculations: pivot, ATR(D), 1H EMAs, swing pivots, ATR ratios.
5. Bias engine → `bias`, `confidence`.
6. AYA Line resolution (per chosen mode).
7. Invalidation level + full-body 1H close detector.
8. Target projection.
9. Pullback / OTE zone box.
10. Liquidity pools + sweep detector.
11. MSS + reclaim detector.
12. Market state classifier.
13. Drawing layer — lines, boxes, labels (anti-clutter: redraw on update).
14. Alerts: `bias_flip`, `invalidation`, `tp_hit`, `pullback_tag`,
    `sweep_reclaim`.
15. Dashboard table render.

---

## 5. Guardrails Encoded in the Script

| Guardrail                        | How it is enforced                                       |
|----------------------------------|-----------------------------------------------------------|
| Wicks never invalidate           | Full-body % filter (`body ≥ 0.6 × range`) on the 1H close |
| Minimum 1:4 RR                   | RR box hatched + warning when geometry fails              |
| No trade in weak momentum        | Dashboard shows `STAND DOWN`, signals suppressed          |
| No reversal without 4-step seq.  | Reclaim engine gates re-entry                             |
| Targets die with the bias        | Drawing layer clears TP labels on invalidation            |
| Single in-flight bias            | State machine — only one of {BULL, BEAR, NEUTRAL}         |

---

## 6. Roadmap Beyond v1

- v1.1 — session presets (London / NY AM / NY PM) auto-anchor.
- v1.2 — volume-profile POC / VAH / VAL overlay as confluence.
- v1.3 — alert-bundle JSON payload for webhook → execution bot.
- v1.4 — back-test harness via `strategy()` clone with the same logic core.
- v2.0 — adaptive `R`-multiple targets driven by realised volatility regime.

---

> "Capital preservation creates longevity. Longevity creates opportunity."
