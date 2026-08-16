# AXIOM

**A**daptive e**X**ecution & **I**nstitutional **O**rder-flow **M**apping

A non-repainting, self-calibrating institutional price-action framework designed to replace
Smart Money Concepts (Order Blocks, FVG/IFVG, BOS/CHoCH, CISD, Liquidity Sweeps,
Premium/Discount) with a single deterministic, causally-sequenced, score-gated decision system.

Version 1.0 — logic specification (implementation-agnostic; targets closed-source Pine Script v6).

---

## Table of Contents

1. [Philosophy & Why AXIOM Beats SMC](#1-philosophy--why-axiom-beats-smc)
2. [Architecture Overview](#2-architecture-overview)
3. [Layer 0 — Measurement Substrate](#3-layer-0--measurement-substrate)
4. [Engine 1 — Institutional Intent Detection Engine (IIDE)](#4-engine-1--institutional-intent-detection-engine-iide)
5. [Engine 2 — Adaptive Imbalance Engine (AIE)](#5-engine-2--adaptive-imbalance-engine-aie)
6. [Engine 3 — Macro Structure Engine (MSE)](#6-engine-3--macro-structure-engine-mse)
7. [Engine 4 — State-Shift Trigger Engine (SSE)](#7-engine-4--state-shift-trigger-engine-sse)
8. [Engine 5 — Confirmation & Decision Engine (CDE)](#8-engine-5--confirmation--decision-engine-cde)
9. [Engine 6 — Multi-Timeframe Confluence Layer (MTC)](#9-engine-6--multi-timeframe-confluence-layer-mtc)
10. [Engine 7 — Liquidity & Clutter Control (LCC)](#10-engine-7--liquidity--clutter-control-lcc)
11. [Engine 8 — Live Risk & Trade Management Desk (RMD)](#11-engine-8--live-risk--trade-management-desk-rmd)
12. [The Sequence Lock — Master Setup FSM](#12-the-sequence-lock--master-setup-fsm)
13. [Non-Repainting Guarantees](#13-non-repainting-guarantees)
14. [Performance Budget](#14-performance-budget)
15. [Settings Architecture](#15-settings-architecture)
16. [Visual Language](#16-visual-language)
17. [Changelog vs Classic / "Elite" SMC](#17-changelog-vs-classic--elite-smc)
18. [Default Parameters & Regime Adaptation](#18-default-parameters--regime-adaptation)
19. [Validation Protocol](#19-validation-protocol)

---

## 1. Philosophy & Why AXIOM Beats SMC

### 1.1 The four structural defects of SMC

SMC is not wrong about *what* matters — institutional participation, imbalance, and structural
transition are real. It is wrong about *how it measures them*. Four defects recur in every
implementation, including the premium "Elite" packages:

**Defect 1 — Binary pattern matching instead of measurement.**
An SMC order block is a shape: "last down candle before an up move." A shape has no magnitude.
The bar that absorbed a genuine institutional bid and the bar that formed because a retail stop
cluster got tripped in a dead session are the *same shape*. SMC therefore produces zones of wildly
different quality with identical visual weight. AXIOM never classifies on shape alone: every
object carries a continuous 0–100 score derived from participation, effort, geometry, and location,
and shape is a necessary-but-insufficient precondition.

**Defect 2 — Independent primitives with no causal ordering.**
In SMC, an order block, an FVG, a BOS, and a sweep each fire on their own trigger. Any two of them
overlapping is retroactively narrated as "confluence." With four primitives each firing a few times
per hundred bars, coincidental overlap is *guaranteed* — this is the actual source of SMC's noise,
and no amount of per-primitive filtering fixes it, because the combinatorics of independent events
are the problem. AXIOM's central innovation is the **Sequence Lock**: a setup does not exist unless
the stages occur *in causal order, each inside a bounded expiry window*. Signal count collapses by
roughly an order of magnitude and the survivors share a common generating mechanism rather than a
coincidence.

**Defect 3 — Fixed thresholds on non-stationary series.**
"Body ≥ 60%", "displacement > 1.5×ATR", "gap > 5 pips" — every SMC filter hardcodes constants
against distributions that change with asset, session, and volatility regime. A 72% body ratio is
unremarkable on Bitcoin at 3am and exceptional on EURUSD in the London fix. AXIOM replaces every
fixed constant with a **dual gate: an absolute floor AND a rolling percentile of that same metric's
own recent distribution.** The system self-calibrates to whatever it is attached to. This is what
makes one parameter set work across FX, indices, metals, and crypto on any timeframe.

**Defect 4 — Ghost state and soft repainting.**
SMC zones linger after invalidation ("mitigated but still drawn"), get re-tested three times until
one works, and pivot-based structure labels appear at bar `t−N` while only becoming knowable at bar
`t`. Combined with `lookahead_on` HTF requests in many scripts, historical charts flatter the method
in ways live trading never reproduces. AXIOM enforces **monotone state machines with immutable birth
bars, one-shot test rights, and instant death on invalid test**, plus a hard prohibition on
look-ahead HTF access.

### 1.2 The five principles AXIOM is built on

| Principle | Statement | Consequence |
|---|---|---|
| **P1 — Measure, don't match** | Every primitive is a scored measurement, not a shape | Continuous quality grading; Tier-1 means something |
| **P2 — Causality over coincidence** | Confluence must be *sequential*, not simultaneous | ~10× fewer signals, shared generating mechanism |
| **P3 — Self-calibration** | Thresholds are percentiles of local distributions | One config for all assets/timeframes/regimes |
| **P4 — Monotone determinism** | State only advances; birth bars are immutable | Zero repainting, by construction rather than by audit |
| **P5 — Scarcity is a feature** | A hard signal budget forces ranking, not accumulation | Solves analysis paralysis structurally |

### 1.3 The order-flow insight SMC misses entirely: Initiative vs Absorption

Every SMC "order block" is treated as a passive limit-order zone. But bars carry two
distinguishable signatures, and conflating them is why SMC zones fail unpredictably:

- **Initiative participation** — high volume, wide range, high body ratio, close near the extreme.
  Aggressive market orders lifting/hitting through the book. This *creates* imbalance and marks the
  **direction** of intent. Its footprint is the displacement leg, not the origin.
- **Absorption participation** — high volume, *compressed* range, large opposing wick, close pushed
  back against the thrust. Passive limit orders soaking up aggression without price progress. This
  marks **where** intent was filled — the true zone.

The highest-probability institutional footprint is a specific *couplet*: **absorption at the origin,
immediately followed by initiative away from it.** Absorption alone is a failed defence.
Initiative alone leaves no re-entry level. SMC's "last opposing candle" rule captures this couplet
by accident, sometimes, with no way to tell when it did. AXIOM measures both halves explicitly
(`AbsorptionScore` at origin, `Cost-of-Reversal` on the leg) and requires both — which is the single
largest source of its win-rate edge over shape-matched order blocks.

### 1.4 What "superior" claims this spec does and does not make

**Defensible by construction, verifiable by inspection:**
- Strictly fewer signals than any SMC configuration at equal lookback (Sequence Lock + Signal
  Scarcity Governor make this arithmetic, not opinion).
- Zero repainting under the guarantees in §13 — auditable line by line.
- Asset/timeframe portability without re-tuning (§3.4 self-calibration).
- Deterministic, reproducible decisions including on opposing setups (§8.4), which SMC leaves to
  discretion entirely.

**Requires empirical validation, not asserted here:**
- Any specific win rate, expectancy, or profit factor. Higher win-rate *potential* follows from
  stricter joint conditioning — each additional independent gate raises the conditional prior of the
  survivors — but the realised number is a property of a given market, timeframe, and period.
  Anyone quoting a win rate for a framework rather than for a tested instrument-period is selling
  something. §19 specifies the protocol that produces honest numbers.

---

## 2. Architecture Overview

Strict one-way data flow. No engine reads downstream state; no cycles; single pass per bar.

```
              ┌──────────────────────────────────────────────┐
              │  LAYER 0 · Measurement Substrate             │
              │  bar anatomy · ATR normalisation · ranks      │
              │  VWID delta proxy · regime classifier         │
              └───────────────────┬──────────────────────────┘
                                  │  normalised metrics
        ┌─────────────────────────┼─────────────────────────┐
        ▼                         ▼                         ▼
┌───────────────┐        ┌────────────────┐        ┌────────────────┐
│ MSE (E3)      │        │ IIDE (E1)      │        │ AIE (E2)       │
│ Macro         │───────▶│ Intent Nodes   │◀──────▶│ Imbalance      │
│ Structure     │ regime │ Tier 1/2/3     │ overlap│ Channels A/B/C │
└───────┬───────┘        └────────┬───────┘        └────────┬───────┘
        │                         │                         │
        │              ┌──────────▼─────────────────────────▼────────┐
        │              │ MTC (E6) HTF confluence · zone upgrades      │
        │              │ LCC (E7) merge · sweep-gated liquidity · cap │
        │              └──────────┬──────────────────────────────────┘
        │                         │  POI set (ranked, capped)
        └────────────────────────▶│
                       ┌──────────▼──────────┐
                       │ SEQUENCE LOCK (§12) │  monotone FSM, windowed
                       └──────────┬──────────┘
                                  │
                       ┌──────────▼──────────┐
                       │ SSE (E4) State-Shift│  origin break + HTF align
                       └──────────┬──────────┘
                                  │
                       ┌──────────▼──────────┐
                       │ CDE (E5) Confirm    │  edge retest · entry mode
                       │        Arbitrate    │  opposing-setup arbitration
                       └──────────┬──────────┘
                                  │
                       ┌──────────▼──────────┐
                       │ RMD (E8) Risk Desk  │  size · SL/TP · panel
                       └─────────────────────┘
```

**Object model.** Three persistent object classes, each a fixed-capacity ring buffer of records:

```
IntentNode      { id, birthBar, dir, proximal, distal, killLine, mid,
                  score, tier, gates[], state, testCount, htfBacked,
                  mergedFrom[], corPct, absScore, expiryTravel }
ImbalanceChannel{ id, birthBar, dir, top, bottom, ce, maxFill,
                  grade, state, invertedAt, hostNodeId }
Setup           { id, dir, stage, stageBar, nodeId, imbId, shiftAnchor,
                  entry, sl, tp1, tp2, score, state, entryMode }
```

`state` fields are **monotone enums** — transitions only ever move forward:

```
IntentNode.state      : FORMING → ARMED → TESTED → CONSUMED → DEAD
ImbalanceChannel.state: ARMED → PARTIAL → CE_BREACH → DEAD | INVERTED
Setup.stage           : 0 → 1 → 2 → 3 → 4 → 5 → 6 → 7  (or → EXPIRED)
```

Any object reaching `DEAD` / `EXPIRED` is never resurrected. This single rule eliminates ghost
zones, re-test farming, and the entire class of "it worked on the third touch" hindsight bias.

---

## 3. Layer 0 — Measurement Substrate

Everything downstream consumes normalised, dimensionless quantities. This layer is why AXIOM is
asset-agnostic.

### 3.1 Bar anatomy (confirmed bars only)

```
ON CONFIRMED BAR i:
  rng      = high - low
  IF rng <= 0: rng = syminfo.mintick        // doji / gap guard, never divide by zero
  body     = abs(close - open)
  bodyRat  = body / rng                      // [0,1]
  upWick   = high - max(close, open)
  dnWick   = min(close, open) - low
  closeLoc = (close - low) / rng             // [0,1]  1 = closed on high
  atr      = ATR(atrLen)                     // atrLen default 14, Wilder
  rngN     = rng / atr                       // volatility-normalised range
  volEff   = volume / rngN                   // volume per unit normalised range
                                             //   HIGH volEff = absorption signature
                                             //   LOW  volEff = initiative / thin drive
```

**Volume availability guard.** Spot FX and some CFD feeds report synthetic or zero volume.
Detect once and degrade gracefully rather than silently producing garbage:

```
volumeUsable = (count of last 200 bars with volume > 0) >= 190
               AND stdev(volume, 200) / avg(volume, 200) > 0.05

IF NOT volumeUsable:
    // Tick-count proxy is unavailable in Pine; substitute a geometric surrogate
    surrogateParticipation = prank(rngN * (1 + bodyRat), 200)
    // Reallocate the Participation weight (20) into Effort (+10) and Geometry (+10)
    // Flag the panel: "SYNTHETIC VOLUME — participation surrogate active"
```

Never fabricate a volume rank on a feed without volume; say so on the panel and reweight.

### 3.2 Volume-Weighted Intent Delta (VWID)

A cheap, defensible signed-flow proxy — no lower-timeframe requests, therefore no repaint risk.
Rationale: a bar closing near its high after a wide range with high volume distributes most of that
volume to the bid side; the close's position within the range is the best single-bar estimate of net
aggression available from OHLCV.

```
FUNCTION barDelta(i):
    pressure = 2 * closeLoc[i] - 1              // [-1, +1]
    conviction = 0.5 + 0.5 * bodyRat[i]         // [0.5, 1] — wick-heavy bars discounted
    RETURN volume[i] * pressure * conviction

FUNCTION VWID(N):                                // N default 8
    RETURN sum(barDelta, N) / max(sum(volume, N), epsilon)   // [-1, +1]
```

`VWID` is used for (a) intent-direction agreement, (b) absorption/initiative disambiguation, and
(c) the divergence veto in §5.4. It is *not* real tick delta and is never labelled as such
anywhere in the UI — call it what it is.

### 3.3 Adaptive percentile ranking (O(1) amortised)

```
FUNCTION prank(value, seriesId, W):
    // Maintained as a fixed-size ring buffer per metric, W default 200.
    // Insert on confirmed bar, evict oldest; count-below is computed on a
    // bounded loop of W elements ONLY when the metric is actually requested
    // this bar (lazy evaluation), otherwise cached from last computation.
    RETURN countBelow(value, ring[seriesId]) / W        // [0,1]
```

Metrics ranked: `volume`, `rngN`, `bodyRat`, `volEff`, `CoR`, `gapSizeN`, `swingAmpN`.

### 3.4 The Dual Gate — the core self-calibration primitive

Every threshold in AXIOM is expressed this way. Absolute floor prevents percentile gates from
passing garbage in dead markets (in a flat market the 90th-percentile bar is still noise);
percentile prevents fixed floors from failing on regime change.

```
FUNCTION dualGate(value, absFloor, pctFloor, metricId):
    RETURN (value >= absFloor) AND (prank(value, metricId, W) >= pctFloor)
```

Example — the body-ratio gate replacing SMC's "60–72% body":

```
strongBody = dualGate(bodyRat, 0.68, 0.80, "bodyRat")
// Requires ≥68% body AND top-20% of this instrument's own recent body ratios.
// On a low-volatility FX session this self-raises; on crypto expansion it stops
// admitting every third bar.
```

### 3.5 Regime classifier

Four regimes drive every adaptive threshold table in §18.

```
ON CONFIRMED BAR:
  netMove   = abs(close - close[R])                  // R default 20
  pathLen   = sum(rng, R)
  efficiency = netMove / max(pathLen, eps)           // [0,1] Kaufman-style
  volPct    = prank(atr, "atr", 200)
  atrSlope  = (atr - atr[R]) / atr[R]

  regime =
    efficiency >= 0.34 AND volPct >= 0.45            → TREND
    efficiency <  0.18 AND volPct <  0.55            → BALANCE
    atrSlope   >= 0.25 AND volPct >= 0.70            → EXPANSION
    atrSlope   <= -0.20 AND volPct <  0.40           → CONTRACTION
    otherwise → previous regime (hysteresis: no flip without 3 consecutive
                                confirming bars, prevents regime chatter)
```

Regime is also a **hard trade veto** input: `CONTRACTION` with `volPct < 0.20` suppresses all new
setups (dead-tape filter — this alone removes a large share of SMC's losing signals, which cluster
in low-volatility chop where zones are dense and moves cannot reach targets).

### 3.6 Displacement leg detection (shared primitive)

Used by IIDE, AIE inversion, and MSE breaks. One definition, one implementation, three consumers —
guaranteeing the "perfect synchronization" requirement rather than hoping for it.

```
FUNCTION isDisplacementLeg(startIdx, endIdx, dir):
    bars = endIdx - startIdx + 1
    IF bars > maxLegBars: RETURN false               // default 5

    net   = dir * (close[endIdx] - open[startIdx])
    netN  = net / atr
    path  = sum(rng, startIdx..endIdx)
    legEff = abs(net) / max(path, eps)
    purity = count(bars closing in dir) / bars
    volN   = avg(prank(volume) over leg bars)

    RETURN  net > 0
        AND dualGate(netN, dispAbsATR, dispPct, "legNetN")   // 1.6 / 0.75
        AND legEff >= legEffMin                              // 0.55
        AND purity >= purityMin                              // 0.66
        AND volN   >= legVolMin                              // 0.60
```

### 3.7 Cost-of-Reversal (CoR) — replaces "freshness"

SMC's freshness is binary (untested / mitigated). It says nothing about how *hard* it would be for
price to reclaim the level. CoR quantifies the effort the market expended leaving the zone —
effort that must be repaid to invalidate it. High-CoR zones are structurally expensive to reverse
and are the ones worth waiting for.

```
FUNCTION costOfReversal(legStart, legEnd):
    effort = 0.0
    FOR i IN legStart..legEnd:
        effort += rngN[i] * (0.5 + prank(volume[i], "volume", 200))
    RETURN effort / (legEnd - legStart + 1)          // per-bar normalised effort

corPct = prank(CoR, "cor", 100)                      // rank vs last 100 legs
```

---

## 4. Engine 1 — Institutional Intent Detection Engine (IIDE)

*Replaces Order Blocks.* Output: `IntentNode` objects, tiered.

### 4.1 Detection pipeline

```
STEP 1 — Leg trigger
  On each confirmed bar, test whether a displacement leg ENDED here:
      FOR L IN 2..maxLegBars:
          IF isDisplacementLeg(i-L+1, i, dir) → candidate leg found, take
             the LONGEST qualifying L (captures full impulse, not a fragment)
  No leg → exit. This is the cheap early-out that keeps the engine O(1)-ish;
  the expensive scoring below runs on <2% of bars.

STEP 2 — Origin cluster identification  (replaces "last opposing candle")
  Walk backwards from legStart-1 while bars satisfy the CONSOLIDATION test:
      inCluster(j) = rngN[j] <= clusterRngMax (0.9)
                     AND NOT closed beyond the cluster extreme in leg dir
      Stop at first bar failing the test, or after maxClusterBars (default 4).
  If zero bars qualify, use the single last opposing-close bar (SMC fallback),
  but apply a −8 score penalty: a clean absorption cluster is materially
  stronger evidence than one lonely candle, and the score should say so.

  clusterHigh = max(high) over cluster
  clusterLow  = min(low)  over cluster
  For BULLISH node:  proximal = clusterHigh, distal = clusterLow
  For BEARISH node:  proximal = clusterLow,  distal = clusterHigh
  mid      = (proximal + distal) / 2
  killLine = distal -/+ killBuf * atr                     // 0.15 ATR default

STEP 3 — Absorption scoring at origin (the half SMC never measures)
  absScore = 0..100:
     +30  prank(volEff over cluster) >= 0.70        // volume without progress
     +25  opposingWickRatio >= 0.35                 // rejection tail present
             opposingWickRatio = (dir>0 ? dnWick : upWick) / rng, cluster max
     +20  prank(volume over cluster) >= 0.65        // participation present
     +15  cluster range compression: avg(rngN) <= 0.85
     +10  cluster closes cluster-internally (no close beyond extreme)

STEP 4 — Geometry / width sanity
  widthN = (proximal - distal) magnitude / atr
  REJECT if widthN > maxWidthATR (1.8)     // a 3-ATR "zone" is not a zone,
                                           // it is an admission of ignorance
  REJECT if widthN < minWidthATR (0.10)    // sub-noise zone, unusable stop

STEP 5 — Score, tier, arm
```

### 4.2 Intent Score (0–100)

```
FUNCTION intentScore(node):
  // ---- Participation (20) ---------------------------------------------
  pPart = 20 * clamp01( (prank(legVol,"volume") - 0.50) / 0.45 )

  // ---- Effort / Cost-of-Reversal (20) ---------------------------------
  pEff  = 20 * clamp01( (corPct - 0.45) / 0.50 )

  // ---- Origin absorption quality (15) ---------------------------------
  pAbs  = 15 * (absScore / 100)

  // ---- Geometry (15) --------------------------------------------------
  pGeo  = 15 * ( 0.5 * clamp01((bodyRatMax - 0.60)/0.35)
               + 0.3 * clamp01(opposingWickRatio / 0.50)
               + 0.2 * (1 - clamp01((widthN - 0.3)/1.2)) )   // tighter = better

  // ---- Flow agreement (15) --------------------------------------------
  pFlow = 15 * clamp01( dir * VWID(8) / 0.35 )

  // ---- Location (15) — replaces naive Premium/Discount ----------------
  //  SMC halves the dealing range and calls it a day. AXIOM measures where
  //  price sits inside the ACTIVE structural range (MSE swing bounds),
  //  ATR-normalised, and additionally rewards distance from the crowded mid.
  rangeHi = MSE.activeSwingHigh ; rangeLo = MSE.activeSwingLo
  pos     = (proximal - rangeLo) / max(rangeHi - rangeLo, eps)    // [0,1]
  locRaw  = dir > 0 ? (1 - pos) : pos                             // discount for longs
  edgeBonus = clamp01(abs(pos - 0.5) / 0.35)                      // reward extremes
  pLoc  = 15 * (0.7 * locRaw + 0.3 * edgeBonus)

  RETURN pPart + pEff + pAbs + pGeo + pFlow + pLoc                // 0..100
```

### 4.3 Tier promotion with mandatory gates

Score alone cannot buy Tier-1. A node may score 84 and still be capped at Tier-2 if any hard gate
fails. This is deliberate: the gates encode conditions where high scores are known to be
misleading, and no weighted sum should be allowed to average them away.

```
HARD GATES (all mandatory for TIER_1):
  G1  score           >= t1Score            (78)
  G2  prank(legVol)   >= 0.80               participation not merely present but ranked
  G3  corPct          >= 0.75               expensive to reverse
  G4  MSE.state       agrees with dir       no counter-structure Tier-1, ever
  G5  MTC.htfBias     agrees with dir       (or htfBias == NEUTRAL and allowNeutral)
  G6  node.state      == ARMED (untested)   freshness absolute
  G7  regime          != CONTRACTION_DEAD
  G8  no ARMED opposing node overlapping this node's range
                                            (contested level = no A+ claim)
  G9  absScore        >= 55                 absorption half of the couplet present
  G10 an AIE channel of grade A or B overlaps or is adjacent within adjATR (0.5)
                                            — the initiative half, verified

TIER ASSIGNMENT:
  all G1..G10            → TIER_1   ("A+", drawn, alertable, tradeable)
  score >= t2Score (62)  → TIER_2   (drawn thin, watchlist only, no trigger)
  else                   → TIER_3   (not drawn by default; diagnostics mode only)
```

Expected Tier-1 frequency at defaults: roughly 1 per 150–400 bars per direction. That is the
intended scarcity — an "A+ setup" appearing six times a session is not an A+ setup.

### 4.4 Smart Freshness & instant mitigation simulation

The one-shot rule: a node receives exactly **one** test opportunity. This is the direct fix for
SMC's ghost zones and its most consequential behavioural difference.

```
ON EVERY CONFIRMED BAR, FOR EACH node WHERE state IN {ARMED, TESTED}:

  touched = (dir > 0) ? (low  <= node.proximal) : (high >= node.proximal)
  killed  = (dir > 0) ? (close < node.killLine) : (close > node.killLine)

  // --- A. Structural death: close beyond kill line. Immediate, unconditional.
  IF killed:
      node.state = DEAD ; removeDrawing(node) ; RETURN

  // --- B. Deep wick without close-through: penetration accounting
  IF touched:
      penetration = (dir>0) ? (node.proximal - low) : (high - node.proximal)
      depthFrac   = penetration / max(abs(node.proximal - node.distal), eps)

      IF node.state == ARMED:
          node.state    = TESTED
          node.testBar  = bar_index
          node.testDepth = depthFrac
      ELSE:
          // Second touch of an already-tested node → node is spent.
          // No "third time lucky". This is the single largest false-signal
          // reduction versus SMC, which happily re-signals a level 4 times.
          node.state = DEAD ; removeDrawing(node) ; RETURN

  // --- C. Reaction verdict on the tested node (evaluated within K bars)
  IF node.state == TESTED AND bar_index - node.testBar <= reactWindow (3):
      reaction = (dir>0) ? (close - node.proximal) : (node.proximal - close)
      IF reaction >= reactMinATR * atr (0.55) AND dir*VWID(3) > 0:
          node.reactionOK = true       // eligible to feed Sequence Lock stage 4
      ELSE IF bar_index - node.testBar == reactWindow:
          node.state = DEAD            // tested and failed to react → dead
          removeDrawing(node)

  // --- D. Penetration-quality veto
  IF node.testDepth > maxTestDepth (0.75):
      // Price cut ~all the way through without closing beyond: the zone is
      // hollow. Treat as failed even if a bounce follows.
      node.state = DEAD ; removeDrawing(node)

  // --- E. Travel-based expiry (replaces bar-count expiry)
  //  Bar counts are meaningless across timeframes; ATR-travel is not.
  node.travel = max(node.travel, abs(close - node.proximal) / atr)
  IF node.travel > expiryTravelATR (12) AND node.state == ARMED:
      node.state = DEAD ; removeDrawing(node)   // price left and never came back
```

---

## 5. Engine 2 — Adaptive Imbalance Engine (AIE)

*Replaces FVG + IFVG.* Output: graded `ImbalanceChannel` objects.

### 5.1 Volatility-normalised detection

```
ON CONFIRMED BAR i (three-bar formation, i-2 / i-1 / i):

  BULLISH candidate: low[i] > high[i-2]
      top = low[i] ; bottom = high[i-2]
  BEARISH candidate: high[i] < low[i-2]
      top = low[i-2] ; bottom = high[i]

  gapSize  = top - bottom
  gapSizeN = gapSize / atr

  // ---- Gate 1: size (dual gate, materially stricter than SMC's "any gap")
  IF NOT dualGate(gapSizeN, gapAbsATR (0.30), gapPct (0.70), "gapSizeN"): REJECT

  // ---- Gate 2: the middle bar must be a genuine displacement bar
  IF NOT ( dualGate(bodyRat[i-1], 0.62, 0.75, "bodyRat")
           AND rngN[i-1] >= 1.10
           AND prank(volume[i-1], "volume") >= 0.60 ): REJECT

  // ---- Gate 3: directional purity of the 3-bar sequence
  IF NOT ( all three closes advance in dir
           AND closeLoc[i-1] in dir's favourable third ): REJECT

  // ---- Gate 4: not already inside a same-direction ARMED channel
  //      (prevents stacked duplicate channels in one impulse — SMC draws six)
  IF overlapsExistingChannel(top, bottom, dir, overlapTol 0.60): MERGE, don't add
```

### 5.2 Grading

```
gradeScore =
    30 * clamp01((gapSizeN - 0.30) / 0.90)
  + 25 * clamp01((prank(volume[i-1]) - 0.55) / 0.40)
  + 20 * clamp01((bodyRat[i-1] - 0.60) / 0.35)
  + 15 * clamp01(dir * VWID(5) / 0.35)
  + 10 * (createdInsideDisplacementLeg ? 1 : 0)

grade =  gradeScore >= 76 → A     (A+ imbalance: eligible for Tier-1 confluence)
         gradeScore >= 58 → B     (usable confluence, not sufficient alone)
         else            → C     (suppressed by default, never drawn)
```

### 5.3 Fill tracking, 50% rendering, strict invalidation

Default rendering is the **50% zone** (`ce` to the far edge collapsed): a gap that has been half
consumed has, in practice, done its job of rebalancing, and drawing the full original box overstates
remaining edge.

```
ce = (top + bottom) / 2

ON EACH CONFIRMED BAR for ARMED / PARTIAL channel:
  filled   = (dir>0) ? (top - min(low, top)) : (max(high, bottom) - bottom)
  fillFrac = clamp01(filled / gapSize)
  ch.maxFill = max(ch.maxFill, fillFrac)          // monotone; never decreases

  // Progressive shrink: the live channel is only the UNFILLED remainder.
  IF dir > 0: ch.top    = min(ch.top,    high_of_deepest_penetration)
  ELSE:       ch.bottom = max(ch.bottom, low_of_deepest_penetration)

  IF ch.maxFill >= 0.50: ch.state = CE_BREACH      // half consumed
  IF (dir>0 ? close < ce : close > ce):
      ch.state = DEAD                              // CLOSE through CE = dead, hard
      → hand to inversion evaluator (§5.4) before removing the drawing
  IF ch.maxFill >= 1.0: ch.state = DEAD
```

Note the asymmetry, which is intentional: a *wick* to CE degrades the channel; a *close* beyond CE
kills it. SMC generally treats any touch of CE as mitigation, which discards still-valid channels,
or treats full fill as required, which keeps dead ones alive. Closes are decisions; wicks are noise.

### 5.4 Inversion logic (IFVG) — suppressed unless triply confirmed

Bare inversion is one of SMC's noisiest primitives: every dead gap becomes an opposing signal, so a
choppy session manufactures a wall of contradictory inversions. AXIOM permits inversion only when
the *manner* of destruction was itself institutional.

```
ON channel death by close-through:

  invGates:
    I1  the through-move qualifies: isDisplacementLeg(deathBar-L+1, deathBar, -dir)
    I2  through-close depth >= invDepthATR (0.45) * atr beyond the far edge
    I3  LOCATION: the channel sits at or beyond a liquidity level (LCC) that was
        SWEPT within sweepLookback (12) bars — destruction at a liquidity
        objective, not mid-range noise
    I4  MSE state has flipped to -dir OR was already -dir
    I5  VWID(5) * (-dir) > 0.15                    // flow confirms the flip
    I6  |VWID| not diverging: the inversion drive is not on falling participation
        (prank(volume) over through-leg >= 0.60)

  IF count(I1..I6 passed) == 6:
      ch.state = INVERTED ; ch.dir = -dir
      ch.top/bottom retained; treated thereafter as a -dir imbalance of grade
      = min(original grade, B)         // inversions never rate A; they are
                                       // second-hand evidence by nature
  ELSE:
      ch.state = DEAD ; removeDrawing(ch)          // auto-suppress weak inversion
```

---

## 6. Engine 3 — Macro Structure Engine (MSE)

*Replaces BOS / CHoCH.* Output: `state`, `activeSwingHigh/Low`, `lastBreak`.

### 6.1 ATR-filtered swing detection

SMC's `pivothigh(n,n)` fires on any local extreme, so a 3-bar wiggle in a 200-pip range produces a
"structure point," and micro-BOS traps follow. AXIOM requires a swing to be *materially* significant
in ATR terms *and* separated in time.

```
STATE: lastPivotType (HIGH|LOW), lastPivotPrice, lastPivotBar,
       provHigh, provHighBar, provLow, provLowBar

ON CONFIRMED BAR i:
  // Track provisional extremes since last confirmed pivot
  IF high[i] > provHigh: provHigh = high[i] ; provHighBar = i
  IF low[i]  < provLow : provLow  = low[i]  ; provLowBar  = i

  // Confirm a swing HIGH only when price has retraced enough FROM it
  IF lastPivotType == LOW:
      retrace  = provHigh - low[i]
      retraceN = retrace / atr
      legAmpN  = (provHigh - lastPivotPrice) / atr

      IF  retraceN >= swingRetraceATR (1.20)                       // absolute
      AND retrace  >= swingRetraceFrac (0.33) * (provHigh - lastPivotPrice)
      AND legAmpN  >= dualGate(legAmpN, swingAmpATR (1.50), 0.55, "swingAmpN")
      AND (provHighBar - lastPivotBar) >= minPivotSep (3)
      AND (i - provHighBar) >= rightBars (2)                       // confirmation lag
      THEN
          CONFIRM swing high at (provHighBar, provHigh)
          // NOTE: birth bar of this pivot object is i, NOT provHighBar.
          // It is *drawn* at provHighBar but all logic uses birth bar i. §13.
          lastPivotType = HIGH ; lastPivotPrice = provHigh
          lastPivotBar  = provHighBar ; provLow = low[i] ; provLowBar = i

  // Symmetric for swing LOW
```

Two independent noise suppressors, both required: an ATR-scaled retracement (so wiggles don't
qualify) and an ATR-scaled leg amplitude (so tiny legs don't qualify).

### 6.2 Break classification — displacement-gated

```
ON CONFIRMED BAR i:
  bullBreak = close > lastSwingHigh + breakBufATR (0.10) * atr
  bearBreak = close < lastSwingLow  - breakBufATR * atr

  // MANDATORY: the breaking move must itself be a displacement leg.
  // Structure that is "broken" by a drifting 0.3-ATR close is not broken;
  // it is being probed. This gate removes most micro-structure traps.
  IF bullBreak AND NOT isDisplacementLeg(breakLegStart, i, +1): IGNORE, no state change
  IF bearBreak AND NOT isDisplacementLeg(breakLegStart, i, -1): IGNORE

  CLASSIFY:
    prior state bullish AND bullBreak → CONTINUATION_BULL   (SMC: BOS)
    prior state bearish AND bullBreak → REVERSAL_BULL       (SMC: CHoCH)
    prior state bullish AND bearBreak → REVERSAL_BEAR
    prior state bearish AND bearBreak → CONTINUATION_BEAR

  // Reversal requires MORE evidence than continuation — asymmetric burden of
  // proof, because reversal calls are where SMC bleeds most.
  REVERSAL additionally requires:
      R1  break displacement netN >= revDispATR (2.0)   // vs 1.6 continuation
      R2  the broken swing was itself a CONFIRMED pivot (not provisional)
      R3  VWID(8) sign agrees with new direction
      R4  a Tier-1 or Tier-2 node formed in the new direction within revWindow
          (10) bars — reversals must leave a footprint, not just a print

MSE.state ∈ { BULL_EXPANSION, BULL_RETRACE, BEAR_EXPANSION, BEAR_RETRACE, BALANCE }
  EXPANSION: within contWindow (8) bars of a confirmed break in that direction
  RETRACE  : post-break, price pulling back toward last node/imbalance
  BALANCE  : no confirmed break within balanceWindow (30) bars OR regime == BALANCE
```

### 6.3 Synchronization contract

The three engines share state through a single explicit contract, enforced by construction rather
than by convention:

1. **Single displacement definition** (§3.6). IIDE legs, AIE middle bars, and MSE breaks are all
   measured by the same function. A leg that creates a Tier-1 node and a leg that breaks structure
   cannot disagree about whether displacement occurred.
2. **Single ATR instance** shared by all engines — no engine may use a private ATR length.
3. **Single swing range** (`activeSwingHigh/Low`) feeds IIDE's location term and LCC's liquidity
   detection, so "discount" means the same thing everywhere.
4. **Evaluation order is fixed** per bar: `Layer0 → MSE → IIDE → AIE → MTC → LCC → FSM → SSE → CDE → RMD`.
   No engine reads a value produced later in the same bar; where it needs one, it reads last bar's.

---

## 7. Engine 4 — State-Shift Trigger Engine (SSE)

*Replaces CISD (Change In State of Delivery).* Fires only inside the Sequence Lock.

### 7.1 Origin-break precision

CISD's weakness is a loose definition of "origin." AXIOM defines the origin set precisely: the
consecutive run of opposing-close bars immediately preceding the reaction from the POI. Breaking the
*open* of the first bar of that run is the exact moment the prior delivery sequence is negated —
that is the shift, and nothing weaker counts.

```
PRECONDITION: Sequence Lock at STAGE 4 (valid POI touch + reaction registered)

FUNCTION findShiftAnchor(dir, touchBar):
    // For a BULLISH setup, walk back from the reaction bar over the run of
    // DOWN-closing bars; the anchor is the OPEN of the FIRST bar in that run.
    j = reactionStartBar
    WHILE j > touchBar - anchorLookback (6)
          AND (dir > 0 ? close[j] < open[j] : close[j] > open[j]):
        j = j - 1
    anchorBar = j + 1
    RETURN open[anchorBar]

ON CONFIRMED BAR:
  shiftBroken = (dir > 0) ? close > anchor + shiftBufATR (0.08) * atr
                          : close < anchor - shiftBufATR * atr

  SHIFT GATES (all mandatory):
    S1  shiftBroken on a CLOSED bar (never intrabar — this is where most
        "CISD indicators" repaint)
    S2  the breaking bar: dualGate(bodyRat, 0.55, 0.65, "bodyRat")
    S3  MTC.htfBias agrees with dir                    // mandatory HTF alignment
    S4  hostNode.tier == TIER_1 AND hostNode.reactionOK
    S5  hostImbalance.grade IN {A} (or A-equivalent after §12 relaxation table)
    S6  barsSince(touchBar) <= shiftWindow (8)         // shift must be prompt;
                                                       // a slow shift is drift
    S7  price has not violated hostNode.killLine at any point since touch
    S8  dir * VWID(4) > 0

  IF all pass: emit SHIFT event, advance FSM to STAGE 5, record shiftAnchor,
               shiftBar, shiftHigh/Low (extremes of the shift leg)
```

### 7.2 Visual

Ultra-light by default: a single fill between `anchor` and the shift-leg extreme at 92%
transparency, plus a 1px dotted anchor line. No labels, no boxes, no gradient. The shift is a
*trigger*, not a level to admire; heavy rendering here is the main source of chart clutter in
CISD indicators.

---

## 8. Engine 5 — Confirmation & Decision Engine (CDE)

### 8.1 Final-edge retest rule

After a shift, the entry is not the shift bar (chasing) and not any arbitrary retracement. It is a
retest of the **final edge** — the surviving proximal boundary after all merges and shrinks, which
is the only price where the remaining unfilled institutional interest actually sits.

```
FUNCTION finalEdge(setup):
    // The zone may have merged (LCC) or shrunk (AIE fill tracking) since birth.
    // The edge is recomputed from CURRENT surviving geometry, never from the
    // original box. This is the "final zone edge only" requirement.
    e = setup.dir > 0 ? max(node.proximal, imb.top_surviving)
                      : min(node.proximal, imb.bottom_surviving)
    RETURN e

VALID RETEST (all mandatory):
  V1  price trades to within retestTolATR (0.12) * atr of finalEdge — or beyond,
      but WITHOUT closing beyond killLine
  V2  the retest bar closes back in dir (rejection close), closeLoc in the
      favourable 45% of range
  V3  retest occurs within retestWindow (10) bars of the shift
  V4  retest LOW (bull) / HIGH (bear) does not exceed shiftAnchar by more than
      retestOvershoot (0.35) * atr  — a deep retest means the shift was weak
  V5  dir * VWID(3) > 0 on the retest bar
  V6  no opposing SHIFT event occurred between shift and retest
```

### 8.2 Entry mode arbitration (market vs pending)

```
ON CONFIRMED RETEST (V1..V6 passed):
    edge = finalEdge(setup)
    dist = abs(close - edge) / atr

    IF dist <= marketProxATR (0.30):
        entryMode = MARKET
        entry     = close                     // at bar close, confirmed
    ELSE IF dist <= pendingMaxATR (1.20):
        entryMode = PENDING_LIMIT
        entry     = edge +/- spreadBufATR (0.05) * atr    // in dir's favour
        pendingExpiry = bar_index + pendingLife (8)
        // Cancelled if: expiry reached, killLine closed through, opposing
        // shift fires, or arbitrator returns SWITCH.
    ELSE:
        entryMode = NONE
        REJECT — price ran too far from the edge; the R:R that justified this
                 setup no longer exists. Do not chase. Mark setup EXPIRED.
```

### 8.3 Stop, targets, and the R-sanity veto

```
SL:
  slRaw  = dir > 0 ? node.distal - slBufATR (0.20) * atr
                   : node.distal + slBufATR * atr
  stopN  = abs(entry - slRaw) / atr

  // R-SANITY VETO — rejects both over-tight and over-wide stops.
  IF stopN < minStopATR (0.45): REJECT   // stop inside noise, guaranteed churn
  IF stopN > maxStopATR (2.50): REJECT   // zone too wide for a sane size

TP1: nearest opposing LCC liquidity level in dir, else entry + 1.5R
TP2: opposing MSE swing extreme, or nearest opposing HTF POI (MTC), else 3.0R

RR VETO: IF (TP1 - entry)/R < minRR1 (1.20) → REJECT setup entirely.
         A structurally beautiful setup with 0.8R to the first objective is a
         losing trade with good manners.
```

### 8.4 Opposing-Setup Arbitrator

The component SMC has no equivalent of. When a bullish and a bearish setup both qualify — which
happens at range boundaries and during reversals — SMC leaves the trader to "use discretion,"
i.e. to flip-flop. The arbitrator resolves it deterministically, with hysteresis so it cannot
oscillate.

```
FUNCTION effectiveScore(setup):
    // A setup's authority DECAYS with age and with adverse excursion.
    ageDecay   = exp( -ageBars / decayTau (40) )                 // → 0.37 @ 40 bars
    // Adverse excursion penalty (only once live)
    IF setup.state == ACTIVE:
        adverse = clamp01(MAE_in_R / 1.0)
        favour  = clamp01(MFE_in_R / 2.0)
        excursionFactor = 1.0 - 0.45 * adverse + 0.25 * favour
    ELSE:
        excursionFactor = 1.0
    premiseFactor = setup.premiseIntact ? 1.0 : 0.55
    RETURN setup.score * ageDecay * excursionFactor * premiseFactor

FUNCTION premiseIntact(setup):
    RETURN  MSE.state agrees with setup.dir
        AND MTC.htfBias agrees OR NEUTRAL
        AND NOT closedBeyond(setup.node.killLine)
        AND NOT opposingShiftConfirmed_since(setup.shiftBar)

FUNCTION arbitrate(current, challenger):
    IF current == NONE:
        RETURN challenger.score >= minTradeScore (70) ? "TAKE" : "WATCH"

    effCur = effectiveScore(current)
    effNew = challenger.score            // fresh; no decay yet

    // --- Guard 1: cooldown. No switching within N bars of the last switch.
    IF barsSince(lastSwitchBar) < switchCooldown (12): RETURN "HOLD"

    // --- Guard 2: a live trade past breakeven is never abandoned for a signal.
    IF current.state == ACTIVE AND current.slAtOrBeyondBE: RETURN "HOLD"

    // --- Guard 3: challenger must clear an absolute floor, not merely beat a
    //             decayed incumbent. Beating a corpse is not evidence.
    IF effNew < minTradeScore (70): RETURN "HOLD"

    // --- Guard 4: dominance margin (hysteresis).
    dominance = effNew - effCur
    IF dominance < switchMargin (12): RETURN "HOLD"

    // --- Guard 5: premise of the incumbent must actually be broken.
    //             Two valid setups can coexist; that is not a reason to switch.
    IF premiseIntact(current): RETURN "WATCH"        // show, do not act

    // --- Guard 6: conflict veto. If BOTH are strong and the incumbent's
    //             premise is intact-ish, the market is undecided → STAND DOWN.
    IF effNew >= 78 AND effCur >= 74: RETURN "STAND_DOWN"

    RETURN "SWITCH"

PANEL SEMANTICS:
  HOLD        → "Hold long. Opposing sell scoring 64 — insufficient."
  WATCH       → "Hold long. Sell setup forming (score 76). Not yet dominant."
  SWITCH      → "Switch to sell. Long premise broken (structure flip + kill line).
                 New score 84 vs 61."
  STAND_DOWN  → "Two-sided conflict. No position. Await resolution above X / below Y."
```

The `STAND_DOWN` state is a genuine addition: a system that must always have an opinion is a system
that will trade range boundaries in both directions and lose on both. Explicitly modelling
"the evidence is balanced, therefore no trade" removes a whole loss category.

---

## 9. Engine 6 — Multi-Timeframe Confluence Layer (MTC)

### 9.1 Automatic HTF ladder

```
FUNCTION autoHTF(chartTF_minutes):
     <= 1   →  15     ( 15×)
     <= 5   →  60     ( 12×)
     <= 15  →  240    ( 16×)
     <= 60  →  1440   ( 24×)
     <= 240 →  10080  ( 42×)
     <= 1440→  10080  (  7×)
     else   →  monthly
// Ratios kept in 7×–42× so the HTF is contextual, not decorative. A 4× HTF
// tells you nothing new; a 200× HTF has no bearing on today.
```

Optional second HTF (`HTF2`, off by default) one rung further out, used **only** for `htfBias`,
never for drawing.

### 9.2 Non-repainting HTF access

```
// MANDATORY FORM — the single most important line in the implementation:
htfClose = request.security(syminfo.tickerid, htfTF, close[1],
                            lookahead = barmerge.lookahead_off)

// close[1] inside the request = the last CLOSED HTF bar.
// lookahead_off = no future leakage.
// Together: the HTF value on any historical bar is exactly what was knowable
// live at that bar. Any implementation without BOTH is repainting, regardless
// of what its description claims.
```

`htfBias` derivation (computed on HTF closed data only):

```
htfBias =  htfMSE.state IN {BULL_EXPANSION, BULL_RETRACE} AND htfClose > htfEMA(21)  → BULL
           htfMSE.state IN {BEAR_EXPANSION, BEAR_RETRACE} AND htfClose < htfEMA(21)  → BEAR
           otherwise → NEUTRAL
```

### 9.3 Dynamic zone upgrade

The requested behaviour — local zones upgrading when an HTF POI later forms over them — is
legitimate *and* non-repainting, provided the upgrade is stamped at its own birth bar and never
back-applied to bars before it. This distinction matters: the upgrade is new information arriving,
not history being rewritten.

```
ON NEW HTF POI CONFIRMED (at the HTF bar's close, i.e. knowable now):
  FOR EACH local node WHERE state IN {ARMED} AND dir == htfPOI.dir:
      overlap = intervalOverlap(node.[distal,proximal], htfPOI.[distal,proximal])
      overlapFrac = overlap / min(node.width, htfPOI.width)

      IF overlapFrac >= htfOverlapMin (0.35):
          node.htfBacked   = true
          node.htfUpgradeBar = bar_index          // immutable stamp
          node.score       = min(100, node.score + htfBonus (6))
          node.borderWidth = 2                    // thicker
          node.label       = node.label + " ★"    // star
          re-evaluate tier (may promote TIER_2 → TIER_1 if G1..G10 now all pass)

  // Downgrade is FORBIDDEN. If the HTF POI later dies, the local node keeps its
  // stamp and its score. Removing an upgrade retroactively would repaint the
  // historical record of why a decision was made.
```

HTF POIs themselves are **not drawn** by default (confluence filter only). Optional
`Show HTF POIs` renders them as unfilled dashed outlines, max 2 per direction, so the chart never
carries two competing zone sets.

---

## 10. Engine 7 — Liquidity & Clutter Control (LCC)

### 10.1 Sweep-gated liquidity

Equal highs/lows are *detected* continuously but *drawn* only after they are swept. An unswept
equal-high is a hypothesis; a swept one is a completed event with a known implication.

```
DETECTION (silent):
  Cluster confirmed swing extremes whose prices agree within eqTolATR (0.15)*atr
  and which are separated by >= minPivotSep bars. Require >= 2 members
  (>= 3 promotes to "major", weight ×1.5).
  Store as a hidden LiquidityLevel { price, memberCount, lastTouchBar, swept }

SWEEP CONFIRMATION (this is when it becomes visible):
  S1  wick pierces the level by >= sweepPierceATR (0.10) * atr
  S2  the SAME bar (or within sweepReclaim (2) bars) CLOSES back on the origin
      side of the level                       // pierced and rejected
  S3  prank(volume) on the piercing bar >= 0.55
  IF S1..S3: level.swept = true ; level.sweptBar = bar_index ; DRAW as
             a short dotted "swept" segment with a small ⌫ marker.
             Feed the sweep to AIE inversion gate I3 and to Sequence Lock stage 1
             as a context booster (+4 score).
```

Unswept levels remain invisible. This removes the horizontal-line thicket that SMC liquidity tools
produce while keeping every level that actually mattered.

### 10.2 Zone merging

```
ON EACH BAR (bounded loop over active nodes, ≤ maxNodes):
  FOR each pair (a, b) of ARMED same-direction nodes:
      gapN = distance between nearest edges / atr
      IF gapN <= mergeGapATR (0.35) OR intervalsOverlap(a, b):
          merged.proximal = dir > 0 ? max(a.proximal, b.proximal)
                                    : min(a.proximal, b.proximal)
          merged.distal   = dir > 0 ? min(a.distal, b.distal)
                                    : max(a.distal, b.distal)
          // Score is NOT averaged — confluence of two real zones is stronger
          // than either, but sub-additive (they may share one cause).
          merged.score = min(100, max(a.score, b.score)
                                  + mergeBonus (5) * (min(a,b).score / 100))
          merged.birthBar = min(a.birthBar, b.birthBar)     // preserve seniority
          merged.state    = strictest of the two             // TESTED beats ARMED
          merged.tier     = re-evaluate G1..G10
          IF merged width > maxWidthATR (1.8): DO NOT MERGE — keep separate
                 // merging must not manufacture an unusable mega-zone
```

### 10.3 Display limit — proximity-prioritised

```
zoneDisplayLimit  (default 4 per direction, single setting for all zone types)

RANKING KEY for visibility:
  key = (tier == TIER_1 ? 0 : 1)                       // tier first
      , distanceATR = abs(price - node.proximal)/atr   // then proximity
      , -score                                          // then quality

KEEP the top `zoneDisplayLimit` per direction. Hidden zones remain FULLY ACTIVE
in logic — visibility and validity are decoupled. This is essential: hiding a
zone must never change a signal, or the chart's appearance becomes part of the
strategy.
```

---

## 11. Engine 8 — Live Risk & Trade Management Desk (RMD)

### 11.1 Universal position sizing

One formula, one per-asset-class value lookup. This is where most indicators quietly break on
non-FX instruments.

```
riskCash  = accountEquity * riskPercent / 100
stopDist  = abs(entry - sl)                              // price units

// valuePerPointPerUnit = currency value of 1.0 price-unit move per 1 unit of size
size = riskCash / (stopDist * valuePerPointPerUnit)

ASSET CLASS RESOLUTION (auto-detected from syminfo.type + syminfo.currency,
                        with manual override):

  FX (syminfo.type == "forex"):
      contractSize = 100_000 (standard lot)
      pipSize      = quote currency == JPY ? 0.01 : 0.0001
      // Direct quote (XXXUSD):   pipValue = pipSize * contractSize
      // Indirect (USDXXX):       pipValue = pipSize * contractSize / rate
      // Cross:                   convert via quote/account FX rate
      stopPips = stopDist / pipSize
      lots     = riskCash / (stopPips * pipValuePerLot)
      DISPLAY: lots to 2dp + units

  METALS:
      XAUUSD: contract 100 oz,  tick 0.01, tickValue 1.00 per contract
      XAGUSD: contract 5000 oz, tick 0.001, tickValue 5.00
      lots = riskCash / (stopDist * contractSize)

  INDICES (CFD):  valuePerPoint = 1.0 * indexCurrencyRate  (per unit/contract)
  INDICES (FUT):  use syminfo.pointvalue directly (ES 50, NQ 20, YM 5, RTY 50)
      contracts = riskCash / (stopDist * syminfo.pointvalue)

  CRYPTO:
      Spot/perp linear: size in BASE units = riskCash / stopDist
      Inverse contracts: size = riskCash * entry / stopDist   (USD-margined inverse)
      DISPLAY base units, notional, and implied leverage.
      LEVERAGE WARNING if notional / equity > leverageWarn (5×).

FALLBACK (unknown symbol type):
      Use syminfo.mintick and syminfo.pointvalue if available; otherwise display
      "SIZE UNAVAILABLE — set contract value manually" rather than a wrong number.
      A confidently wrong lot size is worse than an honest blank.
```

### 11.2 Live updating without repainting

```
ON barstate.islast (or realtime tick):
    recompute lot size, R:R, distances, panel text        // display only
ON barstate.isconfirmed:
    advance trade state machine, record fills, move stops  // logic only

// The invariant: DISPLAY may update every tick; STATE may only advance on
// confirmed bars. Violating this is the most common cause of "it looked
// different yesterday."
```

### 11.3 Trade lifecycle

```
STATES: PENDING → FILLED → TP1_DONE → TP2_DONE | STOPPED | CANCELLED

ON FILLED:
    draw Entry (solid), SL (red), TP1 (dashed), TP2 (dotted)
    optional R:R box: risk region tinted red, reward region tinted green

ON TP1 hit (touch on confirmed bar):
    label TP1 → "TP1 ✓ done" ; strike-through style
    close tp1Fraction (50%)
    move SL → entry + beBufATR (0.10) * atr * dir        // breakeven-plus
    set setup.slAtOrBeyondBE = true                      // arbitrator Guard 2
    engage trailing: SL = max(SL, chandelier(highest(high, trailLen 10)
                                             - trailATRmult (2.0) * atr))

ON TP2 hit:  label "TP2 ✓ done", close remainder, state TP2_DONE
ON SL hit:   state STOPPED, all lines dimmed to 70% transparency, kept for
             `postTradeBars` (20) bars as a record, then removed
```

### 11.4 Trade Guide Panel (mobile-friendly)

Fixed 2-column table, ≤ 9 rows, one screen on a phone. It answers exactly one question:
*what do I do next?*

```
┌─────────────────────────────────────────┐
│ AXIOM · EURUSD · 15m        HTF 4H BULL │
├─────────────────────────────────────────┤
│ Regime      │ TREND (vol 68%)           │
│ Structure   │ BULL_RETRACE              │
│ Setup       │ LONG · Stage 5/7          │
│ Confluence  │ 84 / 100   ████████░░ A+  │
│ Zone        │ T1 ★ HTF-backed 1.0847    │
│ Next step   │ AWAIT RETEST → 1.0847     │
│ Entry/SL    │ 1.0851 / 1.0824  (27p)    │
│ TP1/TP2     │ 1.0892 ✓ / 1.0941         │
│ Size        │ 0.74 lots  (1.0% = $250)  │
│ Opposing    │ SELL 61 → HOLD            │
└─────────────────────────────────────────┘
```

`Next step` is always one imperative sentence drawn from FSM stage:

| Stage | Next step text |
|---|---|
| 1 | `NO SETUP — context only (bias BULL)` |
| 2 | `T1 zone armed at 1.0847 — await imbalance confluence` |
| 3 | `A+ confluence formed — await price return to 1.0847` |
| 4 | `Zone tested, reaction OK — await state shift > 1.0862` |
| 5 | `SHIFT CONFIRMED — await retest of 1.0847 (8 bars left)` |
| 6 | `RETEST VALID — MARKET LONG now, SL 1.0824, 0.74 lots` |
| 7 | `IN TRADE — TP1 done, SL at BE+, trailing active` |

---

## 12. The Sequence Lock — Master Setup FSM

The centrepiece. Every stage has an **expiry window**; a missed window resets the setup rather than
leaving a half-formed pattern lying around to be completed opportunistically later.

```
STAGE 0  IDLE
   → advance when regime != CONTRACTION_DEAD

STAGE 1  CONTEXT                                    window: continuous
   REQUIRE: MSE.state agrees with dir
        AND MTC.htfBias agrees with dir (or NEUTRAL and allowNeutralHTF)
        AND regime IN {TREND, EXPANSION, BALANCE-with-vol}
   BOOST:   +4 if a liquidity sweep against dir occurred within 12 bars
   → STAGE 2

STAGE 2  INTENT                                     window: 30 bars
   REQUIRE: a TIER_1 IntentNode in dir, state == ARMED
   → STAGE 3

STAGE 3  IMBALANCE                                  window: 8 bars from node birth
   REQUIRE: grade-A ImbalanceChannel overlapping the node OR within adjATR (0.5)
        AND same direction
        AND channel.state IN {ARMED, PARTIAL}
   → STAGE 4  (setup is now "A+ ARMED"; alertable as "setup forming")

STAGE 4  APPROACH                                   window: expiryTravel (ATR-based)
   REQUIRE: price touches finalEdge within retestTolATR
        AND node.state transitions ARMED → TESTED (first touch only)
        AND node.reactionOK within reactWindow (3) bars
        AND NOT closedBeyond(killLine)
   → STAGE 5

STAGE 5  STATE SHIFT                                window: shiftWindow (8 bars)
   REQUIRE: SSE gates S1..S8 all pass
   → STAGE 6

STAGE 6  CONFIRMATION                               window: retestWindow (10 bars)
   REQUIRE: CDE V1..V6 all pass
        AND entryMode != NONE
        AND R-sanity + RR vetoes pass
        AND arbitrate(...) IN {TAKE, SWITCH}
   → STAGE 7 (execute)

STAGE 7  ACTIVE — managed by RMD

ANY STAGE → EXPIRED when:
   window exceeded  OR  hostNode.state == DEAD  OR  hostImbalance.state == DEAD
   OR MSE.state flips against dir  OR  MTC.htfBias flips against dir
   OR opposing SHIFT confirmed
EXPIRED setups are terminal. A new setup must begin at STAGE 1 from scratch.
```

### 12.1 Why this produces the order-of-magnitude noise reduction

Let each stage's per-bar pass probability be `p_k`. SMC's effective signal rate is roughly
`Σ p_k` — primitives fire independently and any overlap gets narrated as confluence. AXIOM's is
approximately `Π (p_k · w_k)` where `w_k` is the probability the next stage lands inside its
window. With six stages of moderate individual selectivity, the joint rate falls by one to two
orders of magnitude — and, crucially, the survivors are not just rarer but *mechanistically
coherent*: absorption, then imbalance, then return, then negation of the prior delivery, then
rejection. Each survivor tells one story.

### 12.2 Signal Scarcity Governor

The final answer to analysis paralysis. Even after the Sequence Lock, cap output:

```
maxSignalsPerWindow (default 2 per 100 bars, per direction)

IF signalsInWindow >= maxSignalsPerWindow:
    IF newSetup.score > weakestActiveSignal.score + 8:
        retire the weakest (mark SUPERSEDED, keep on chart dimmed for audit)
        admit the new one
    ELSE:
        suppress newSetup (logged in diagnostics, not drawn, no alert)
```

A hard budget forces the system to *rank* rather than *accumulate*. If two signals is what a
hundred bars deserve, showing seven does not add information — it adds decisions.

---

## 13. Non-Repainting Guarantees

Auditable rules. Each one is checkable by reading the implementation; together they make
repainting structurally impossible rather than merely unobserved.

| # | Guarantee | Enforcement |
|---|---|---|
| **NR1** | All classification on confirmed bars | Every detection guarded by `barstate.isconfirmed`, or reads `[1]`-offset series exclusively |
| **NR2** | No look-ahead HTF | `request.security(..., close[1], lookahead=barmerge.lookahead_off)` is the only permitted form; no exceptions, including for "display only" values |
| **NR3** | No `varip` | Forbidden project-wide. All state in `var`, mutated only on confirmed bars |
| **NR4** | Pivot birth ≠ pivot location | Pivots draw at bar `t−N` but every logic path uses birth bar `t`. Any comparison of the form `barsSince(pivot)` uses birth bar |
| **NR5** | Monotone states | State enums are ordered; transitions assert `new >= old`. Death is terminal |
| **NR6** | One-shot tests | Second touch of a TESTED node kills it. No re-signalling from spent levels |
| **NR7** | Display/logic separation | Ticker-rate updates touch only text, lines, and sizing. Trade state and signals advance only on confirmed bars |
| **NR8** | Monotone fill tracking | `maxFill` never decreases; a channel cannot "un-fill" on a lower-timeframe rendering |
| **NR9** | No retroactive downgrade | HTF upgrades are stamped and permanent (§9.3). Nothing may un-happen |
| **NR10** | No LTF intrabar requests | No `request.security` to a timeframe below the chart for entry precision — the standard vector for historically-perfect entries that never occur live |
| **NR11** | Alert on close only | `alertcondition` / `alert()` fire on confirmed bars, never `alert.freq_all` on forming bars |
| **NR12** | Deterministic order | Fixed engine evaluation order (§6.3); no engine reads same-bar downstream output |

**Self-audit mode** (developer toggle, off in release): logs `bar_index`, object id, and state
transition for every mutation. Replaying the same data must produce a byte-identical log —
diffing a historical replay against a forward-collected log is the definitive repaint test, and it
should be run as a release gate.

---

## 14. Performance Budget

| Resource | Budget | Technique |
|---|---|---|
| `request.security` calls | ≤ 3 | HTF OHLC bundled into one tuple call; HTF2 bias in a second; optional HTF POI in a third |
| Drawing objects | ≤ 60 total | Fixed pools of boxes/lines/labels, mutated via `set_*`, never delete-and-recreate |
| Active objects | nodes ≤ 24, channels ≤ 24, setups ≤ 4 | Ring buffers with eviction by `(state, distance, score)` |
| Per-bar loops | ≤ 3 bounded | One over nodes, one over channels, one over liquidity levels. No history loops |
| Percentile rings | 7 × 200 | Lazy evaluation — a rank is computed only on bars where its gate is actually reached |
| Early-out | ~98% of bars | `isDisplacementLeg` fails fast (2 comparisons) before any scoring runs |
| `max_bars_back` | 500 explicit | Prevents the runtime from inferring a huge window |

**Removed heavy patterns** (common in SMC scripts, all avoidable):
- Nested loops over all historical pivots each bar → replaced by incremental swing state machine.
- `array.sort` per bar for zone ranking → replaced by single-pass max/min selection for the top-`k`.
- Re-drawing every zone every bar → replaced by dirty-flag rendering (only mutated objects redraw).
- Recomputing HTF structure on the chart timeframe → computed once inside a single security call.
- String concatenation for the panel every bar → built only on `barstate.islast`.

---

## 15. Settings Architecture

Every filter independently toggleable. Grouped, with each group collapsed by default except
**Core**. A toggled-off filter must be *neutral*, never *inverted*: disabling a gate makes it pass,
it does not make it a requirement in reverse.

```
▸ CORE
    Direction bias (Both / Long / Short)
    Zone Display Limit ............................ 4
    Min Trade Score ............................... 70
    Signal Scarcity: max signals / 100 bars ....... 2

▸ INSTITUTIONAL INTENT  (IIDE)
    Enable Intent Nodes ........................... on
    Tier-1 score threshold ........................ 78
    Tier-2 score threshold ........................ 62
    ☐ Gate: participation rank ≥ ................. 0.80
    ☐ Gate: Cost-of-Reversal percentile ≥ ........ 0.75
    ☐ Gate: absorption score ≥ ................... 55
    ☐ Gate: require structure agreement .......... on
    ☐ Gate: require HTF agreement ................ on
    ☐ Gate: require imbalance confluence ......... on
    ☐ Gate: no opposing overlap .................. on
    Origin cluster max bars ....................... 4
    Max / min zone width (ATR) .................... 1.8 / 0.10
    Kill-line buffer (ATR) ........................ 0.15
    One-shot test rule ............................ on
    Max test penetration .......................... 0.75
    Travel expiry (ATR) ........................... 12

▸ ADAPTIVE IMBALANCE  (AIE)
    Enable Imbalance Channels ..................... on
    Min gap size (ATR) / percentile ............... 0.30 / 0.70
    Grade A / B thresholds ........................ 76 / 58
    Show grade C .................................. off
    Render mode (Full / 50% / Remaining) .......... 50%
    Death on CE close ............................. on
    ☐ Enable Inversions .......................... on
    ☐ Inversion: require displacement ............ on
    ☐ Inversion: require swept liquidity ......... on
    ☐ Inversion: require structure flip .......... on
    Auto-suppress weak inversions ................. on

▸ MACRO STRUCTURE  (MSE)
    Swing retracement (ATR) ....................... 1.20
    Swing retracement (fraction of leg) ........... 0.33
    Min swing amplitude (ATR) ..................... 1.50
    Min pivot separation (bars) ................... 3
    Break buffer (ATR) ............................ 0.10
    ☐ Require displacement on break .............. on
    ☐ Reversal: stricter burden of proof ......... on
    Show structure labels (Off / Minimal / Full) ... Minimal

▸ STATE SHIFT  (SSE)
    Enable state-shift trigger .................... on
    Anchor lookback ............................... 6
    Shift buffer (ATR) ............................ 0.08
    Shift window (bars) ........................... 8
    ☐ Mandatory HTF alignment .................... on
    Zone opacity .................................. 92%

▸ CONFIRMATION & DECISION  (CDE)
    Retest tolerance (ATR) ........................ 0.12
    Retest window (bars) .......................... 10
    Max retest overshoot (ATR) .................... 0.35
    Market proximity (ATR) ........................ 0.30
    Pending max distance (ATR) .................... 1.20
    Pending life (bars) ........................... 8
    Min R:R to TP1 ................................ 1.20
    Min / max stop (ATR) .......................... 0.45 / 2.50
    ☐ Opposing-setup arbitrator .................. on
    Switch margin ................................. 12
    Switch cooldown (bars) ........................ 12
    ☐ Stand-down on two-sided conflict ........... on

▸ MULTI-TIMEFRAME  (MTC)
    HTF mode (Auto / Manual) ...................... Auto
    Manual HTF .................................... 4H
    Enable HTF2 bias .............................. off
    ☐ Dynamic zone upgrade ....................... on
    HTF overlap minimum ........................... 0.35
    HTF score bonus ............................... 6
    Show HTF POIs ................................. off

▸ LIQUIDITY & CLUTTER  (LCC)
    Show liquidity: Post-sweep only / All / Off .... Post-sweep only
    Equal-level tolerance (ATR) ................... 0.15
    Sweep pierce minimum (ATR) .................... 0.10
    ☐ Merge overlapping zones .................... on
    Merge gap (ATR) ............................... 0.35

▸ RISK DESK  (RMD)
    Account equity ................................ 10000
    Risk % ........................................ 1.0
    Asset class (Auto / FX / Metals / Index / Crypto) Auto
    Manual contract value ......................... 0 (0 = auto)
    TP1 fraction .................................. 50%
    ☐ Breakeven+ after TP1 ....................... on
    ☐ ATR trail after TP1 ........................ on  (len 10, mult 2.0)
    ☐ Show R:R box ............................... on
    ☐ Show Trade Guide Panel ..................... on
    Panel size / position ......................... Small / Top-right

▸ REGIME & ADAPTATION
    ☐ Enable regime adaptation ................... on
    Efficiency lookback ........................... 20
    ☐ Dead-tape veto (vol pct < 0.20) ............ on
    ☐ Session filter ............................. off
    Allowed sessions .............................. London + NY overlap

▸ VISUALS
    Theme (Dark / Light / Auto) ................... Auto
    Palette (Neutral / Cool / Mono) ............... Neutral
    Zone opacity .................................. 88%
    ☐ Show scores on labels ...................... on
    ☐ Diagnostics mode (Tier-3, logs) ............ off
```

---

## 16. Visual Language

Design rule: **the chart shows what is actionable now; everything else is a filter that runs
invisibly.**

- **Bullish zones** — neutral desaturated slate/stone (`#8C9AA6` family), not green. Colour should
  encode *quality*, not direction; direction is already obvious from position. Bearish zones use a
  slightly warmer neutral (`#A6968C`).
- **Tier-1** — 88% transparent fill, 2px solid border, single right-edge label `A+ 84 ★`.
- **Tier-2** — 94% transparent fill, 1px dotted border, no label.
- **State-shift zone** — 92–96% transparent, no border, 1px dotted anchor line only.
- **Imbalance channels** — hatch-free flat fill at 90%, no border, rendered at 50% by default.
- **Swept liquidity** — 1px dotted horizontal segment spanning only sweep→now, with `⌫`.
- **Structure** — `Minimal` mode: a single small `⌃`/`⌄` at confirmed pivots and one thin dashed
  line at the active break level. No `BOS`/`CHoCH` text spam.
- **Trade lines** — entry solid 1px, SL solid red 1px, TP dashed/dotted, done levels struck through
  and dimmed.
- **Theme** — two full palettes, auto-selected via `chart.bg_color` luminance; all opacities
  specified per theme so light-mode zones don't vanish.

Total simultaneous objects at defaults: **≤ 14 visible** (4 nodes × 2 directions, 2 channels,
1 shift, ~3 liquidity, 4 trade lines, 1 panel). This is the answer to analysis paralysis at the
presentation layer, matching the answer at the logic layer.

---

## 17. Changelog vs Classic / "Elite" SMC

**Architecture**
1. `+` **Sequence Lock FSM** — confluence must be *causal and windowed*, not simultaneous. Replaces independent primitive firing; ~1–2 orders of magnitude fewer signals.
2. `+` **Signal Scarcity Governor** — hard signal budget with score-based supersession. New concept; no SMC analogue.
3. `+` **Monotone object state machines** with immutable birth bars and terminal death. Eliminates ghost zones.
4. `+` **Explicit synchronization contract** — one displacement definition, one ATR, one active range, fixed evaluation order.

**Measurement**
5. `+` **Initiative vs Absorption decomposition** (`volEff`, `absScore`) — order-flow distinction SMC does not make at all.
6. `+` **Cost-of-Reversal** — effort-based zone durability replacing binary freshness.
7. `+` **VWID signed-flow proxy** — honestly labelled OHLCV-derived, no LTF requests.
8. `+` **Dual Gate** on every threshold (absolute floor + rolling percentile). Replaces all hardcoded constants.
9. `+` **Regime classifier** (efficiency + vol percentile + hysteresis) driving adaptive thresholds and a dead-tape veto.
10. `+` **Volume-feed usability detection** with declared surrogate and weight reallocation, instead of silently ranking synthetic volume.

**Intent Nodes vs Order Blocks**
11. `~` Origin **cluster** detection replaces "last opposing candle" (with an explicit score penalty when only a single candle qualifies).
12. `~` Body-ratio gate raised from 60–72% fixed to **≥68% AND ≥80th percentile**, self-raising.
13. `+` **100-point Intent Score** with published weights; **10 mandatory hard gates** for Tier-1 that a high score cannot override.
14. `+` **One-shot test rule** — second touch kills the node. Removes SMC's re-test farming.
15. `+` **Penetration-quality veto** — >75% hollow penetration invalidates even if a bounce follows.
16. `+` **Reaction verdict window** — a tested node that fails to react within 3 bars dies.
17. `+` **ATR-travel expiry** instead of bar-count expiry (timeframe-invariant).
18. `+` **Width sanity band** — rejects both mega-zones and sub-noise zones.
19. `~` **Location term** measured inside the active MSE range with an edge bonus, replacing naive 50% premium/discount.

**Imbalance vs FVG/IFVG**
20. `~` **ATR-normalised, dual-gated gap size** replaces "any 3-bar gap."
21. `+` **Middle-bar displacement requirement** + 3-bar directional purity.
22. `+` **A/B/C grading**; grade C never drawn; only grade A satisfies Tier-1 confluence.
23. `~` **50% (CE) default rendering** with progressive shrink to the unfilled remainder.
24. `~` **Wick degrades / close kills** asymmetry at CE, replacing binary mitigation.
25. `+` **6-gate inversion filter** (displacement, depth, swept-liquidity location, structure flip, flow, participation); weak inversions auto-suppressed and inversions capped at grade B.
26. `+` **Stacked-channel merging** — one channel per impulse, not six.

**Structure vs BOS/CHoCH**
27. `~` **ATR-filtered swings** requiring both retracement magnitude and leg amplitude, plus minimum pivot separation.
28. `+` **Displacement-gated breaks** — drift closes past a swing are ignored entirely.
29. `+` **Asymmetric reversal burden of proof** (higher displacement + confirmed pivot + flow agreement + footprint node within 10 bars).
30. `~` Five-state regime ledger replacing binary bullish/bearish.

**Trigger vs CISD**
31. `~` **Precise origin definition** (open of first bar of the opposing-close run) rather than a loose "sequence origin."
32. `+` **8 mandatory shift gates**, including non-negotiable HTF alignment and a promptness window.
33. `+` **Tight linkage** — shift cannot fire without a Tier-1 node and grade-A imbalance already in place.
34. `~` **Ultra-light rendering** by default.

**Confirmation & decision**
35. `+` **Final-edge retest rule** computed from *surviving* geometry after merges and shrinks.
36. `+` **Automatic market-vs-pending arbitration** by post-confirmation distance, with a no-chase rejection band.
37. `+` **R-sanity veto** (min and max stop in ATR) and **min-R:R veto**.
38. `+` **Opposing-Setup Arbitrator** with score decay, excursion penalty, premise test, cooldown, dominance margin, and Hold/Watch/Switch output. No SMC analogue.
39. `+` **STAND_DOWN state** for two-sided conflict — explicitly modelling "no trade."

**MTF**
40. `+` **Automatic HTF ladder** constrained to 7×–42× ratios.
41. `+` **Dynamic zone upgrade** (thicker border + ★ + score bonus) stamped at its own birth bar, with retroactive downgrade forbidden.
42. `~` HTF POIs used as **filters only**, not drawn by default.
43. `+` **Mandated non-repainting HTF form** (`close[1]` + `lookahead_off`) as an auditable rule.

**Liquidity & clutter**
44. `~` **Sweep-gated liquidity display** — unswept levels stay invisible.
45. `+` **Sweep confirmation** requires pierce + reclaim close + participation, and feeds the inversion and context layers.
46. `+` **Sub-additive score merging** with a max-width guard.
47. `+` **Single proximity-prioritised display limit** with **visibility fully decoupled from validity**.

**Risk**
48. `+` **Universal sizing formula** with per-asset-class contract resolution and an explicit "SIZE UNAVAILABLE" fallback instead of a wrong number.
49. `+` **Display/logic tick separation** invariant.
50. `+` **Trade Guide Panel** with a single imperative next step per FSM stage.

**Performance**
51. `−` Removed: historical pivot loops, per-bar sorting, full redraws, per-bar string building, LTF intrabar requests, `varip`.
52. `+` **Fast-fail ordering** — cheapest gates first; heavy scoring on <2% of bars.
53. `+` **Lazy percentile evaluation** and dirty-flag rendering.
54. `+` **Self-audit replay mode** as a release gate for repaint detection.

---

## 18. Default Parameters & Regime Adaptation

### 18.1 Baseline defaults

| Parameter | Default | Sane range | Notes |
|---|---|---|---|
| `atrLen` | 14 | 10–21 | Shared by all engines |
| `rankWindow W` | 200 | 100–500 | Percentile memory |
| `dispAbsATR` | 1.6 | 1.2–2.4 | Displacement floor |
| `dispPct` | 0.75 | 0.65–0.88 | Displacement percentile |
| `legEffMin` | 0.55 | 0.45–0.70 | Path efficiency of leg |
| `purityMin` | 0.66 | 0.60–0.85 | Directional purity |
| `bodyRat` floor / pct | 0.68 / 0.80 | 0.60–0.76 / 0.70–0.90 | Replaces fixed 60–72% |
| `t1Score` / `t2Score` | 78 / 62 | 72–86 / 55–70 | Tier thresholds |
| `corPct` gate | 0.75 | 0.60–0.88 | Cost-of-Reversal |
| `maxWidthATR` / `min` | 1.8 / 0.10 | 1.2–2.5 / 0.05–0.20 | Zone width band |
| `killBufATR` | 0.15 | 0.05–0.30 | Invalidation buffer |
| `maxTestDepth` | 0.75 | 0.60–0.90 | Hollow-penetration veto |
| `reactWindow` / `reactMinATR` | 3 / 0.55 | 2–5 / 0.35–0.90 | Reaction verdict |
| `expiryTravelATR` | 12 | 8–25 | Travel expiry |
| `gapAbsATR` / `gapPct` | 0.30 / 0.70 | 0.20–0.55 / 0.60–0.85 | Imbalance size |
| `gradeA` / `gradeB` | 76 / 58 | 70–84 / 50–65 | Imbalance grades |
| `swingRetraceATR` | 1.20 | 0.8–2.0 | Swing filter |
| `swingAmpATR` | 1.50 | 1.0–2.5 | Swing filter |
| `minPivotSep` | 3 | 2–8 | Swing separation |
| `breakBufATR` | 0.10 | 0.03–0.25 | Break buffer |
| `revDispATR` | 2.0 | 1.6–3.0 | Reversal burden |
| `shiftWindow` | 8 | 5–15 | Shift promptness |
| `retestTolATR` | 0.12 | 0.05–0.25 | Edge tolerance |
| `retestWindow` | 10 | 6–20 | Retest patience |
| `marketProxATR` | 0.30 | 0.15–0.50 | Market-entry band |
| `pendingMaxATR` | 1.20 | 0.8–2.0 | No-chase boundary |
| `minStopATR` / `max` | 0.45 / 2.50 | 0.3–0.7 / 1.8–3.5 | R-sanity |
| `minRR1` | 1.20 | 1.0–2.0 | R:R veto |
| `switchMargin` | 12 | 8–20 | Arbitrator hysteresis |
| `switchCooldown` | 12 | 6–30 | Arbitrator hysteresis |
| `decayTau` | 40 | 20–80 | Score decay |
| `minTradeScore` | 70 | 62–80 | Absolute execution floor |
| `maxSignalsPer100` | 2 | 1–5 | Scarcity governor |
| `riskPercent` | 1.0 | 0.25–2.0 | Position sizing |

### 18.2 Regime adaptation table

Multipliers applied to the baselines when `Enable regime adaptation` is on. The logic: in trend,
lean on continuation and loosen patience; in balance, demand more evidence and less R; in expansion,
raise every displacement bar so ordinary volatility doesn't masquerade as intent; in contraction,
mostly stand aside.

| Parameter | TREND | BALANCE | EXPANSION | CONTRACTION |
|---|---|---|---|---|
| `dispAbsATR` | ×1.00 | ×0.85 | ×1.35 | ×0.75 |
| `t1Score` | −2 | +4 | +0 | +8 |
| `gapAbsATR` | ×1.00 | ×0.85 | ×1.30 | ×0.80 |
| `swingRetraceATR` | ×1.10 | ×0.85 | ×1.30 | ×0.80 |
| `retestWindow` | ×1.20 | ×0.80 | ×1.00 | ×0.70 |
| `minRR1` | ×1.00 | ×1.25 | ×1.10 | ×1.40 |
| `maxStopATR` | ×1.00 | ×0.85 | ×1.30 | ×0.80 |
| `maxSignalsPer100` | 3 | 2 | 2 | 1 |
| Counter-trend setups | blocked | allowed | blocked | blocked |
| Reversal setups | Tier-1 only | allowed | Tier-1 only | blocked |
| Dead-tape veto | — | — | — | active if volPct<0.20 |

### 18.3 Asset-class starting points

Self-calibration means these are nudges, not re-tunes. If a genuine re-tune is needed for a new
instrument, the percentile gates are doing their job wrong and the *gates* should be fixed, not the
constants.

| Class | Adjustments | Rationale |
|---|---|---|
| **FX majors** | `dispAbsATR ×0.90`, session filter on (London/NY) | Lower relative volatility; Asian session is structurally noise |
| **FX crosses / exotics** | `killBufATR ×1.3`, `minStopATR ×1.2` | Wider spreads and slippage |
| **Indices (cash)** | Gap handling on; suppress the first 2 bars after the open | Overnight gaps distort ATR and manufacture false imbalances |
| **Index futures** | Baseline | Continuous, honest volume |
| **Gold / Silver** | `dispAbsATR ×1.10`, `maxWidthATR ×1.15` | Impulsive, wick-heavy behaviour |
| **Crypto majors** | `rankWindow 300`, `expiryTravelATR ×1.4`, no session filter | 24/7; longer trends; fatter tails |
| **Crypto alts** | `t1Score +4`, `maxStopATR ×0.85`, leverage warning on | Thin books, violent reversals |

### 18.4 Timeframe guidance

| Chart TF | Auto HTF | Notes |
|---|---|---|
| 1m | 15m | Raise `minPivotSep` to 5; spread cost dominates — expect few Tier-1s |
| 5m | 1H | Session filter strongly recommended |
| 15m | 4H | The system's natural home: ~1–3 A+ setups per instrument per week |
| 1H | Daily | `expiryTravelATR ×1.3` |
| 4H | Weekly | Reduce `maxSignalsPer100` to 1 |
| Daily+ | Weekly/Monthly | `rankWindow 100` (limited history), widen `retestWindow` |

---

## 19. Validation Protocol

Superiority claims deserve evidence, not assertion. Before this framework is called better than
anything, it should clear these gates.

**V1 — Repaint audit (pass/fail, blocking).**
Enable self-audit mode. Collect a forward log over ≥ 500 live bars. Reload the chart on the same
range and collect the historical log. Diff must be empty. Any difference is a repaint bug and
blocks release regardless of performance.

**V2 — Signal-count comparison (quantitative, expected to pass trivially).**
On identical data, count SMC-primitive confluence events vs AXIOM Stage-7 executions. Confirm the
reduction is 10×+ and inspect a sample of what was excluded — every exclusion should be explicable
by a named gate. If exclusions look arbitrary, a gate is miscalibrated.

**V3 — Gate ablation study (the honest test).**
For each of the 10 Tier-1 gates and each veto, run with it disabled. A gate that does not improve
expectancy or does not reduce variance is **decoration and should be deleted**, not shipped as a
toggle. Expect 2–4 of the gates in this spec to fail this test on any given market; ship the
survivors and say which ones they were.

**V4 — Out-of-sample and cross-asset.**
Calibrate percentile windows on 2015–2020, evaluate 2021–2026. Test ≥ 3 instruments per asset class.
The self-calibration claim is falsified if per-asset tuning turns out to be necessary — report that
outcome if it happens.

**V5 — Cost realism.**
Include spread, commission, and slippage at the 75th percentile of observed values, not the median.
Tight-stop setups near `minStopATR` are the ones cost destroys, and they are also the ones a naive
backtest flatters most.

**V6 — Arbitrator regression.**
Isolate periods with two-sided setups. Compare arbitrator decisions against a
hold-everything baseline and a switch-always baseline. If `STAND_DOWN` does not beat both, the
conflict veto needs re-tuning or removal.

Report all six. A framework that publishes its ablation study is worth more than one that publishes
a win rate.

---

*End of specification. Implementation targets Pine Script v6, closed-source distribution.
No code is included by design.*
