# Smart SR Zones [JOAT] — engineering audit

Source reviewed: the published Pine v6 source of
[`NXuV5E1i`](https://www.tradingview.com/script/NXuV5E1i-Smart-SR-Zones-JOAT/),
1,109 lines, MPL-2.0, © officialjackofalltrades. A verbatim copy is kept at
`reference/smart_sr_zones_v1_original.pine` so every line reference below is
checkable.

Reviewed the way a perception stack gets reviewed: what does each stage
*measure*, what does it *assume*, and what happens at the boundary where the
assumption fails.

---

## What is genuinely good

These are real engineering decisions, not decoration, and v2 keeps all of them.

| # | What | Why it's right |
|---|------|----------------|
| 1 | **Zones are bands, not lines** (`pad = a * 0.25`, L362) | Liquidity sits in a range. Line-based S/R indicators are unfalsifiable — any level is "close enough". |
| 2 | **ATR-relative tolerance** rather than fixed ticks or percent (L333) | The one scale-invariance decision that lets the same settings work on ES and on a 3-cent altcoin. |
| 3 | **Composite pivot weight** — volume × wick × age decay (L305–313) | Correctly rejects the naive "all pivots are equal" model. The *shape* of the formula is sound. |
| 4 | **Live-break flag** (`isLiveBreak`, L426) | Deliberately catches the born-dead case: a zone that clusters into existence already breached. This is a subtle bug class and the author saw it. |
| 5 | **Minimum spacing between touches** (L338–342) | The intent — don't let ten bars of chop inflate a touch count — is exactly right. (The *implementation* is broken; see C3.) |
| 6 | **State inheritance across rebuilds** (`inheritState`, L491) | Recognises that a rebuilt zone should not forget it was already tested. Right instinct, wrong layer. |
| 7 | **Preset ladder** (Scalp/Local/Swing/Major) | Good product decision. Most users cannot tune six coupled parameters and shouldn't have to. |
| 8 | **Bounded draw budget** — clear-and-redraw on `barstate.islast` only (L940) | Keeps the object count well under Pine's 500-object ceiling. Many published S/R scripts blow this. |
| 9 | **Signals default OFF** | Refreshingly honest. Ships the levels, not a signal salad. |

---

## Critical defects

### C1 — The zone set is destroyed and rebuilt on every pivot
`resZones.clear()` / `supZones.clear()` at L517 and L524, inside the
`if newHighPivot or newLowPivot` block.

Every confirmed pivot wipes both pools and re-derives them from the whole
buffer. There is no persistent object, so there is no such thing as *this
level*. `inheritState` (L491) tries to paper over it by copying `lastTouch`
and the ZOI flag onto whichever new zone lands nearest, but `touches`,
`firstBar`, and the entire break history are silently recomputed.

Consequences: zone edges jitter, ages reset, and — worst — a level that
genuinely still exists is archived as *dropped* whenever the rebuild happens
to cluster it half an ATR away.

This is detection-without-tracking. Nothing in the design says *the same
level, one bar later*.

### C2 — Clustering is greedy, seed-anchored, and order-dependent
L336: `math.abs(cand.price - seed.price) <= tol`.

Membership is tested against the **seed pivot**, never against the running
cluster centre, and `used[j]` is set permanently the first time a pivot is
claimed. So:

- The oldest pivot in the buffer dictates the cluster for everything near it.
- A pivot that would fit a later, stronger cluster much better can never move.
- Total cluster width is unbounded in one direction and hard-capped in the
  other, depending purely on array order.

Two identical charts differing only in how far back the buffer reaches will
produce different zones.

### C3 — Minimum spacing *splits* levels instead of merging them
L338–342. When a candidate is too close in time to an existing member,
`farEnough := false` and the candidate is **excluded from the cluster
entirely**. It is not marked `used`, so on a later outer iteration it becomes
the **seed of its own zone**.

The stated intent is "don't double-count a touch." The actual behaviour is
"split one real level into two competing zones that then fight for the same
top-N slot." The rapid re-test — the strongest evidence a level exists —
is the exact case that breaks it.

### C4 — `touches` never counts an actual touch
`z.touches` is set once, from `members.size()` (L364), and is never
incremented anywhere. `lastTouch` updates when price enters the box
(L442–455), but the count does not.

The label reads `3x`. It means *three pivots clustered here*, not *price
tested this three times and it held*. Those are different quantities and only
the second one predicts anything. The indicator never observes its own
outcomes.

### C5 — A single close kills a zone permanently
L424: `if na(z.diedBar) and close > z.top`.

No buffer, no confirmation bar, no participation requirement. One close a
tick beyond the edge and the level is dead. Then `isAlreadyBroken` (L521,
L528) blocks it from ever re-entering the active pool.

So the single most common structure in real markets — resistance breaks,
becomes support, gets defended for months — is unrepresentable. The script
even contains retest logic for broken zones (L590–616), which is a tacit
admission that the level still matters; it just refuses to track it.

Every stop-run permanently deletes a good level.

### C6 — The ZOI touch gate is almost certainly inverted
L662: `touchOk = z.touches == minTouches`.

Strict equality against the *minimum*. With the default `minTouches = 2`, a
zone with 3+ clustered pivots can never be a Zone of Interest, no matter how
much volume it absorbed. The headline feature is structurally restricted to
the weakest qualifying zones.

Compounding it, `quietEnough` returns `true` when `lastTouch` is `na`
(L661) — so a zone that has never been touched *at all* passes the
"has been quiet since its last touch" test.

### C7 — Historical pivots are measured with today's ruler
`buildZones` receives the **current** `atr` (L510) and applies
`tol = a * clusterTol` to pivots from arbitrarily far back.

After a volatility expansion, decade-old pivots get merged with a wide
tolerance they never earned. After a compression, real levels get split.
Scale must travel with the measurement; here it is re-applied globally at
read time.

---

## Significant defects

### S1 — Stars are relative, so they mean nothing absolute
`strengthStars` (L196) rates each zone against `maxS` — the strongest zone
*currently on screen*. A chart with nothing but junk levels still displays
★★★ on its least-bad one. There is no threshold at which the indicator says
"none of these are good."

### S2 — Volume evidence is one candle wide, and double-counted
`safeVolume(pivRight)` takes a single bar's raw volume (L242). A level absorbs
inventory over a window, not on one print. Then `volSum` (L357) is a plain sum
over members, so a 5-member cluster beats a 2-member cluster on volume largely
*because* it has more members — and member count is already in the score
through `weightSum`. The same evidence is counted twice.

### S3 — Silent degradation on instruments without volume
`safeVolume` returns `1.0` when volume is `na` (L242) and `volMa` is `na`, so
`volNorm` falls back to `1.0`. On FX, CFDs and most index feeds every
volume-derived term collapses to a constant while the UI continues to display
volume scores, volume-driven opacity, and a volume-gated ZOI. The indicator
does not tell you its main discriminator is switched off.

### S4 — Every zone is the same thickness
`pad = a * 0.25` (L362) — a fixed ±0.25 ATR regardless of how tightly the
member pivots actually agree. A level where five pivots printed within two
ticks and a smear of pivots spread over half an ATR draw identical boxes. The
dispersion of the cluster is computed nowhere, and it is the most direct
measure of how well-defined a level is.

### S5 — Age decay is hardcoded to 200 bars
L311: `decay = 1.0 / (1.0 + age / 200.0)`. Independent of timeframe and of
the pivot width in use. 200 bars is ~3 days on 15m and ~9 months on daily.

### S6 — Signals evaluate on the forming bar
`heldUp = close >= z.bot and close >= open` (L569) and the reject mirror
(L585) run on every tick of the live bar. Markers appear and disappear
intrabar; alerts fire on conditions that are not true at close.

### S7 — Distance filter is in percent
`hideFar` (L44, L754) gates on percent-of-price. 60% is most of the range on
an equity and rounding error on a low-priced crypto pair. The rest of the
script is carefully ATR-relative; this one input is not.

### S8 — History eviction is FIFO
`brokenZones.shift()` at L414 drops the **oldest** archived zone when the
cap of 100 is hit — which is systematically the most significant one, since
old levels that survived that long are old *because* they mattered.

---

## Minor / cosmetic

- **M1 — The ZOI "pulse" does not pulse.** `zoiPulseAdj` (L763) keys off
  `bar_index % 8`, but drawing only happens on `barstate.islast`, where
  `bar_index` is constant between bars. It is a fixed pseudo-random opacity
  offset, not an animation.
- **M2 — `maxVolAcrossActive()` is called twice** (L668–669), and the second
  call runs after the resistance pool has already been mutated, so the two
  sides are normalised against slightly different denominators.
- **M3 — `maxVolAcrossActive` and `maxVolAcross` are byte-identical** (L633,
  L860).
- **M4 — Cost.** `buildZones` is O(n²) with an O(m) inner spacing scan, and
  `trimToTopN` is an O(n²) selection sort — both re-run on every pivot bar
  over the full buffer. With `pivBuffer = 200` this is avoidable work in the
  hundreds of thousands of operations per pivot.
- **M5 — Signal cooldown collides across sides.** `cooldownOk` (L541) keys on
  centre proximity only, so a support and a resistance at similar prices
  suppress each other's signals.
- **M6 — Repainting is not disclosed.** Boxes are drawn from `z.firstBar`,
  the pivot bar — but the pivot is not confirmed until `pivRight` bars later.
  The chart shows the zone existing before it could have been known. This is
  inherent to pivot logic and fine; presenting it without a note is not.

---

## Verdict

The idea is right and several of the individual mechanisms are well chosen.
What is missing is a **temporal model**. v1 is a detector that re-runs from
scratch every frame and never checks its own predictions: nothing persists,
nothing accumulates, nothing is measured against what actually happened.
That single structural gap is what produces C1, C4, C5 and S1 — and it is
what v2 replaces.

See `docs/ALGORITHM.md` for the replacement design and
`pine/smart_sr_zones_v2.pine` for the implementation.
