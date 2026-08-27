# Smart SR Zones v2 — algorithm

The rewrite borrows its structure from an autonomy perception stack, because
support/resistance is the same problem shape: noisy detections arriving one
frame at a time, which have to be associated into persistent objects, scored
under uncertainty, and then checked against what actually happened.

```
 bars ──▶ PERCEPTION ──▶ ASSOCIATION ──▶ FUSION ──▶ DECISION ──▶ VALIDATION
          detections      persistent      P(hold)    hysteresis   reliability
          + features      tracks                     + flip       diagram
```

v1 implemented the first box and half of the fourth. Everything between them
was a full rebuild from scratch on every pivot.

---

## 1. Perception — detections carry their own scale

A confirmed pivot becomes a detection with a feature vector, all of it
measured **at the pivot's own bar**:

| Feature | Definition | Why |
|---|---|---|
| `atrAt` | `ATR(50)` at the pivot bar | The ruler travels with the measurement. Fixes audit **C7**. |
| `relVol` | 3-bar participation around the pivot ÷ its own 50-bar baseline | A level absorbs inventory over a window, not one print. Fixes **S2**. |
| `wickR` | rejection wick ÷ `atrAt` | Kept from v1; the shape was right. |
| `imp` | distance price travelled away from the level during the confirmation window, in ATR | **New.** See below. |

**Post-pivot impulse** is the feature v1 had no notion of. v1 scored the
*candle*; it never scored the *reaction*. A level price fled from at 3 ATR and
a level price drifted past at 0.2 ATR produce identical v1 scores. Impulse
separates them, and it is free — those bars are already in the confirmation
window.

On instruments with no volume feed the engine substitutes normalised true
range as the participation proxy and marks the volume column `n/a` rather than
quietly reporting a constant (fixes **S3**).

---

## 2. Association — tracks, not rebuilds

A level is a persistent object with an id. Each detection is matched to at
most one existing track by gated nearest-neighbour:

```
gate  = max(atrAt · clusterTol, track.halfWidth · 1.5)
match = argmin |track.center − pivot.price|   subject to  distance ≤ gate
```

Matched → the track absorbs it. Unmatched → a new track is spawned.

The gate widens with the track's own width, so a level that legitimately spans
a band keeps collecting its pivots instead of spawning a duplicate beside
itself.

### State update

A recursive weighted mean with Welford's online variance — mathematically the
same estimate v1 recomputed from scratch, at O(1) per detection instead of
O(n²) per pivot bar:

```
w′  = w + wᵢ
δ   = xᵢ − μ
μ′  = μ + (wᵢ/w′)·δ
M2′ = M2 + wᵢ·δ·(xᵢ − μ′)
```

### Zone width is measured, not assumed

```
halfWidth = clamp(kσ · √(M2/w), minPad·ATR, maxPad·ATR)
```

Tight agreement between a level's own pivots draws a thin zone; a smeared
cluster honestly draws a wide one. Fixes **S4**.

### Touch events vs. detections

Pivots closer together than `minSpacing` are folded into **one touch event**:
the price and volume are still absorbed, only `hits` is not incremented. v1
excluded the pivot from the cluster entirely, which let it seed a competing
zone. Fixes **C3**.

### Non-max suppression

On each pivot bar, tracks whose price intervals overlap above `mergeIoU` are
fused — evidence summed, variances combined in parallel form:

```
M2ₐ ← M2ₐ + M2_b + wₐ(μₐ−μ)² + w_b(μ_b−μ)²
```

This is the safety net for whatever the greedy association misses, and it is
the step v1 had nowhere. Fixes **C2**.

### Role is derived, not stored

There is one pool of *levels*. Whether a level is support or resistance is
`center > close`, evaluated live. A broken resistance is automatically a
tracked support. Fixes **C1** and **C5** structurally rather than by special
case.

---

## 3. Fusion — a calibrated probability

Nine normalised features feed a weighted prior:

```
score = Σ wᵢ·fᵢ / Σ wᵢ            fᵢ ∈ [0,1]
```

- pivot count `1 − e^(−(hits−1)/1.8)`
- relative volume, rejection wick, post-pivot impulse (same saturating form)
- cluster tightness `1 − σ/(ATR·clusterTol)`
- recency `1/(1 + age/decayBars)`, where `decayBars` scales with the
  detector width instead of v1's hardcoded 200 (fixes **S5**)
- volumetric prior — the pre-touch field score (§5); the only feature that
  can carry a zone on its own
- higher-timeframe confluence (§6)
- round-number proximity

The prior is mapped into log-odds and combined with the level's **own realised
track record** through a Laplace-smoothed likelihood ratio:

```
logit  = k·(score − mid)  +  β·ln((h + α)/(b + α))
P(hold) = σ(logit)
```

`h` and `b` are held/broke counts for the role the level is currently playing,
plus half-weight on the opposite role — a level that never breaks in either
direction is genuinely more trustworthy than one that only holds from one
side. Laplace smoothing keeps a level with one lucky hold from reading 100%.

Stars use **absolute** bands (70% / 55%), so an all-junk chart shows all
single stars. Fixes **S1**.

---

## 4. Decision — hysteresis, then flip

Every interaction runs a three-state machine per track:

```
IDLE ──price enters zone──▶ TESTING ──▶ HELD / BROKEN / UNRESOLVED ──▶ IDLE
```

- **BROKEN** requires close beyond the far edge by `breakAtr·ATR`, for
  `breakConfirm` consecutive closes, with participation ≥ `breakVolMult`.
  One tick through the edge no longer kills a level.
- **HELD** requires price to retreat `holdAtr·ATR` clear of the zone —
  a bounce has to actually go somewhere to count.
- **UNRESOLVED** — price sat inside the zone past `resolveBars`. This
  contributes **no evidence** rather than being silently scored as a win.
  Refusing to score ambiguous outcomes is the difference between a metric and
  a flattering one.

A confirmed break does not kill the level. It **flips** its role, discounts
its accumulated evidence by `flipDecay` (its character changed, so its history
is worth less), and keeps tracking. Only after `maxFlips` is it retired as
noise. Fixes **C5**, and makes the retest logic v1 bolted on unnecessary.

Real touch counts are now real: `hits` counts pivots, `realTouch` counts
resolved tests, and the label shows both as `3p/2t`. Fixes **C4**.

Everything resolves on closed bars when `confirmBarsOnly` is on. Fixes **S6**.

---

## 5. Volumetric prior field — the pre-touch layer

An ego-shifting occupancy grid over price carrying volume, signed delta,
time-at-price and unconsumed inventory ("fuel") per bin. Four terms — shelf,
velocity, trapped inventory, void adjacency — compose into a prior that needs
**no pivot, no touch and no outcome history**, so a Zone of Interest can be
published before price ever reaches it. Local maxima of the field are seeded
as tracks with `hits = 0`, and the sign of the stranded cohort predicts
whether the level will act as support or resistance on return.

Scored separately from the P(hold) calibration by an ex-ante ledger: of the
calls made *before* price arrived, how many produced the predicted reaction.

Full derivation, parameters and limits: **[`VOLUMETRIC_PRIOR.md`](VOLUMETRIC_PRIOR.md)**.

## 6. Higher-timeframe confluence

HTF pivots are pulled with `lookahead_off` and kept in a small deduplicated
level array. Confluence decays linearly from 1.0 at an exact match to 0 at
`htfTolAtr·ATR`. The HTF defaults to a sensible multiple of the chart
timeframe and is clamped so it can never resolve *below* the chart.

---

## 7. Validation — the part that makes the rest falsifiable

Every resolved test is filed into the probability bucket that was live **at
the moment the test began** — before the outcome was known — and the panel
reports predicted vs. realised hold rate across the whole chart:

```
Reliability   68% vs 64%   n=143
```

Green when the gap is under 7 points, amber under 15, red beyond.

This is shadow-mode evaluation, and it is what a score is worth on its own:
nothing, until something checks it. If the two numbers diverge on your symbol
and timeframe, the model is miscalibrated **there** and the stars should be
discounted accordingly — which is information v1 could not give you, because
it never observed its own outcomes.

The `n=` matters as much as the gap. Under ~30 resolved tests the panel says
`warming up`, and it means it.

---

## 8. Honest mode

`noRepaint` (default on) anchors each zone's box to the bar the pivot was
**confirmed**, not the bar the high or low printed. The zone did not exist
until `pivRight` bars after the extreme, and drawing it earlier back-dates
information you did not have. Turning it off restores v1's cosmetically nicer,
hindsight-flattering rendering. Addresses **M6**.

---

## Parameter reference

| Group | Parameter | Default | Effect |
|---|---|---|---|
| Engine | Strength preset | `Auto` | `Auto` scales the detector to the chart's bar rate |
| Engine | Honest mode | on | Draw from confirmation bar |
| Engine | Closed bars only | on | No intrabar flicker |
| Engine | Hide below P(hold) | 0.00 | Absolute quality gate |
| Engine | Hide farther than | 14 ATR | Distance gate in volatility units, not percent (**S7**) |
| Tracker | Pool size | 36 | Levels held in memory; weakest dead recycled first (**S8**) |
| Tracker | Zone width | 2.0 σ | Data-driven thickness |
| Tracker | Merge IoU | 0.55 | NMS threshold |
| Break | Break buffer | 0.25 ATR | Hysteresis band |
| Break | Confirmation bars | 2 | Consecutive closes required |
| Break | Volume requirement | 1.0× | Participation gate; 0 disables |
| Break | Hold confirmation | 0.35 ATR | Retreat required to score a hold |
| Break | Max flips | 2 | Retire after this many role changes |
| Scoring | Evidence weight β | 0.9 | 0 = pure feature model |
| Scoring | Laplace α | 1.0 | Smoothing on held/broke counts |
| ZOI | Min volumetric prior | 0.55 | Pre-touch gate; replaces v1's `touches == minTouches` (**C6**) |
| ZOI | Min fuel | 0.60 | Unconsumed inventory required to stay armed |
| ZOI | Min distance | 1.0 ATR | A level you are standing in is not a forward target |

---

## Tuning notes

- **Start with weights at defaults and read the reliability row.** If realised
  materially exceeds predicted, the priors are too timid — raise
  `logitK`. If predicted exceeds realised, they are overconfident: lower
  `logitK` or raise `logitMid`.
- **On low-liquidity symbols**, drop `wVol` and `wHVN` toward zero and lean on
  `wImp` and `wTight`. Thin-tape volume is mostly noise.
- **In an expanding-volatility regime** (the dashboard reports it), raise
  `breakAtr` — the buffer is in ATR, but a regime shift can outrun a 50-bar
  ATR for a few sessions.
- `evW = 0` gives the pure feature model, which is the right control to
  compare against when you are deciding whether the evidence term is earning
  its place on your instrument.

---

## Known limits

- **Pivot confirmation lag is irreducible.** A level cannot be known until
  `pivRight` bars after its extreme. Honest mode makes the lag visible; it
  does not remove it.
- **The calibration is in-sample on the visible chart.** It measures whether
  the model is consistent with the history it can see, not whether it
  generalises forward. It is a smoke test, not a backtest.
- **`request.security` on the HTF adds a data request** and is subject to the
  usual HTF bar-close latency.
- **The pool is bounded** at `maxTracks`. On very long histories the weakest
  levels are recycled; this is deliberate, but it means the engine is not a
  complete archive of every level that ever existed.
