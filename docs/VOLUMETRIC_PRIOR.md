# The volumetric prior — finding a Zone of Interest before it is touched

## The problem

Every ZOI definition I have seen, v1's included, is retrospective. v1 required
`touches == minTouches`, a volume share, and a quiet period — all of which are
statements about what has *already happened at* the level. By the time a level
qualifies, the information that made it interesting has been paid out.

The thing a trader actually wants is the opposite: *tell me where price will
react, before it goes there.* That requires a **prior** — a score computable
with zero touches, zero pivots and zero outcome history.

## The insight

An untested level is not interesting because of its geometry. Geometry is the
*shadow* of the thing that matters.

It is interesting because **a known cohort of participants is stranded there**.

- Volume tells you the cohort exists and how big it is.
- Signed order flow tells you which side it is on.
- The distance price has travelled since tells you how much pain it is in.

None of that requires a retest. It is all already in the tape at the moment the
cohort was created. When price comes back to their breakeven, trapped longs
sell into it and trapped shorts buy it back — and that supply or demand *is*
the reaction. It is why untested levels work at all.

So the prior is: **where is inventory stranded, how much of it, on which side,
and how much of it has already got out?**

---

## 1. The substrate: an ego-shifting occupancy grid

A rolling volume profile cannot carry a prior. It throws away its accumulated
state on every rebuild, so by construction it can only describe the past — it
can never carry a charge forward into a level that has not been touched yet.

v2 uses a fixed-resolution price grid that **follows price**. When price
approaches an edge, the grid shifts by whole bins and state slides with it:

```
sh = round((close − gridLo)/binW − N/2)          shift only when |offset| > N/4
new[i] = old[i + sh]                              integer shift — lossless
gridLo += sh · binW
```

Integer shifts are exact, which is the whole reason for choosing a following
grid over a re-binned window. A large volatility regime change (ATR ratio
outside `[0.4, 2.5]`) triggers a nearest-neighbour resample into new bin
geometry rather than a discard.

This is the same construct as an ego-centric occupancy grid in an autonomy
stack, and for the same reason: you want persistent belief about space you are
not currently observing.

Per bin the grid carries `vol`, `dlt` (signed volume), `bars` (time at price),
`fuel`, and `last` (bar index of the most recent visit).

### Delta without tick data

Signed volume uses the Chaikin close-location value:

```
clv   = ((close − low) − (high − close)) / (high − low)     ∈ [−1, 1]
delta = volume · clv
```

Closing at the high of a bar means buyers won that bar. It is the best
directional read available without a tick feed, and it is sufficient here
because what matters is the **sign of a large cohort**, not its exact size.

Volume and delta are spread uniformly across the bins the bar's range covers.

---

## 2. The four prior terms

All four are computable before price ever returns.

### Shelf — `normalise(vol[b])`
Inventory exists here. The plain high-volume node. Necessary but weak alone:
lots of volume trades at prices nobody cares about, simply because price spent
time there.

### Velocity — `normalise(vol[b] / bars[b])`
Volume **per bar** at price. Size traded fast is an aggressive footprint; the
same volume accumulated slowly is drift.

This distinction is the cheapest real edge in the whole field and essentially
no volume-profile tool exposes it. A profile shows you a fat node and cannot
tell you whether it was 200 bars of balanced rotation or nine bars of somebody
being filled.

### Trapped — the core term

```
mid(b)   = binLow + (b + ½)·binW
D        = dlt[b]

adverse  =  D > 0  →  max(0, mid(b) − close)      buyers stranded above
            D < 0  →  max(0, close − mid(b))      sellers stranded below

trapped(b) = |D| · (1 − e^(−adverse/(k·ATR)))
```

A cohort with a known size (`|D|`), a known side (`sign D`) and a known pain
level (`adverse`), which **has not yet had its chance to get out**. The
saturating term means being 5 ATR underwater is not meaningfully worse than
being 3 ATR underwater — past a point they are all just waiting for breakeven.

### Void adjacency — `max over |k|≤span of (1 − normVol[b+k]) · normVol[b]`

A shelf sitting beside a volume vacuum. Price has nothing to lean on crossing
the gap, so it arrives at the shelf fast and in size. Note the multiplication
by the bin's own normalised volume: the tradable object is the **edge** of the
vacuum, not the vacuum itself.

### Composition

```
prior(b) = ( w_shelf·shelf + w_vel·velocity + w_trap·trapped + w_void·void )
           / Σw
           × fuel(b)
```

---

## 3. Fuel — a level has a charge, and it burns

This is what makes the prior decay honestly without waiting for a formal
"test."

Each genuine revisit works off some of the stranded inventory: trapped traders
get their exit, and there are fewer of them next time.

```
on a return to bin b (price was away for > revisitGap bars):
    fuel[b] ← fuel[b] · e^(−burn · v_added / vol[b])
```

A revisit that trades as much volume as was originally stored burns ≈63% of the
charge at `burn = 1.0`. Contiguous accumulation while price is already parked
in the bin does **not** burn fuel — that is the cohort forming, not leaving.

Consequences worth stating plainly:

- A level can be **spent without ever being formally tested**. Price drifting
  through it repeatedly discharges it, and the score falls, correctly.
- A field-born zone is retired on `fuel` rather than on the clock. Its entire
  claim is that nothing has happened there yet; a stale-bars timeout would be
  the wrong retirement criterion.
- The ZOI label shows the gauge directly — `ZOI 84% R` means 84% of the stored
  inventory is unconsumed and the stranded side is expected to supply.

---

## 4. Direction before touch

The sign of the stranded cohort predicts the *role* the level will play on
return, before it plays it:

| | Stranded side | On return they | Level acts as |
|---|---|---|---|
| `D > 0`, price now below | buyers, underwater | sell to get out | **resistance** |
| `D < 0`, price now above | sellers, underwater | buy to cover | **support** |

This falls out of the same number that produced the score, so it costs
nothing, and it is a genuinely forward statement: not "this was resistance"
but "this will act as resistance when you get there."

---

## 5. Zones with no pivots

Local maxima of the prior field are published as tracks with `hits = 0`.

```
peak      prior[b] ≥ prior[b±1], prior[b±2]     strict 5-bin local max
gate      prior[b] ≥ zoiPriorMin
distance  |mid(b) − close| ≥ zoiMinDist · ATR   a level you are standing in
                                                is not a forward target
match     associate() first — a shelf that coincides with a pivot zone
          reinforces it rather than duplicating it
width     full-width-half-maximum of the field peak, so a volumetric zone
          gets a measured thickness exactly as a pivot zone gets its width
          from member dispersion
```

Unmatched peaks become new tracks, drawn with a dotted centre line and a
`vol` tag so you can see at a glance which levels have no swing structure
behind them at all.

In scoring, the prior stands in for the pivot-shape features a field-born zone
cannot have (count, wick, impulse) rather than scoring them as zero, and
`wPrior` adds it as a term for every zone including the pivot-born ones.

### The ZOI gate is now pure

```
ZOI  =  vprior ≥ priorMin
    ∧   fuel   ≥ fuelMin
    ∧   resolvedTests ≤ maxTests
    ∧   barsSinceTouch ≥ quiet
    ∧   |center − close| ≥ minDist · ATR
```

Note what is **not** in it: probability, pivot count, touch count. Every term
is computable before price has ever been there. That is the contract.

---

## 6. Validating a forward claim

A prior that is never scored is astrology. The ledger works like this:

1. A zone is **armed** the bar it is first flagged — while price is away.
2. `armed` records the predicted direction at that moment.
3. When price finally arrives, evaluation opens.
4. **HIT** if price displaces `reactAtr · ATR` in the predicted direction
   within `reactBars`. **MISS** on the opposite displacement or on timeout.

The dashboard reports it separately from the P(hold) calibration:

```
Next ZOI            4218.50  R  84%  2.1 ATR
Prior (pre-touch)   61%  n=37
```

`Prior` is the ex-ante hit rate: of the calls made **before** price got there,
how many produced the predicted reaction. Green ≥ 55%, amber ≥ 45%, red below.
Under n=10 it stays neutral-coloured, because it is not saying anything yet.

Alerts fire on the forward events, not the retrospective ones: `ZOI armed
(pre-touch)`, `ZOI approach` (price closing and still `approachAtr` away),
`ZOI prior confirmed`, `ZOI prior failed`.

---

## 7. Limits, stated honestly

- **The delta proxy is a proxy.** Close-location value gets the sign right far
  more often than chance but it is not tick delta. On instruments with heavy
  auction opens or thin gaps it will mislabel bars. The design leans on it only
  for the sign of an *aggregate* cohort, which is where it is strongest.
- **No volume feed, no trapped term.** On FX and most index CFDs the grid falls
  back to true range as a participation proxy. Shelf and velocity still carry
  meaning; `trapped` becomes noise. Drop `wTrapW` toward zero there — and the
  dashboard's `n/a` volume column tells you when you are in that regime.
- **The grid is finite.** `gridBins × binAtr` ATR of price is all it can hold.
  Structure that leaves the window is gone, by design; `fieldHalf` is the
  intended memory control, not the grid extent.
- **A rescale is lossy.** Nearest-neighbour resampling across a >2.5× ATR
  regime shift smears the field by up to half a bin. Rare, but it is an
  approximation, not a transform.
- **The prior ledger is in-sample on the visible chart** and accumulates
  slowly — a few dozen resolved calls over a long history. Read it as a smoke
  test on whether the field means anything for this symbol, not as a backtest.
- **Peaks near price are suppressed, not scored.** Anything inside
  `zoiMinDist` is invisible to the pre-touch layer. That is deliberate — it
  is a forward-looking layer — but it means the field is silent exactly when
  price is chopping inside a shelf.

---

## Parameter reference

| Parameter | Default | Effect |
|---|---|---|
| Grid bins | 120 | Field resolution |
| Bin height | 0.22 ATR | Grid granularity in volatility units |
| Field refresh | 5 bars | Recompute cadence for prior + candidates |
| Field half-life | 900 bars | How fast old structure fades |
| Revisit gap | 6 bars | Bars away before a return counts as a revisit |
| Inventory burn | 1.0 | Fuel consumed per unit of revisit volume |
| Trapped-pain scale | 1.5 ATR | Underwater distance for a full trapped score |
| Void span | 3 bins | Neighbourhood searched for an adjacent vacuum |
| `wShelf / wVelW / wTrapW / wVoidW` | 1.0 / 1.2 / 1.6 / 0.8 | Field term weights |
| `wPrior` | 1.5 | Prior's weight in the overall zone score |
| Min volumetric prior | 0.55 | The pre-touch gate |
| Min fuel | 0.60 | Charge required to stay armed |
| Min distance | 1.0 ATR | Suppression radius around price |
| Approach warning | 1.5 ATR | Pre-touch alert distance |
| Reaction required | 0.8 ATR / 15 bars | What counts as the prior being right |

## Tuning

- **Read `Prior (pre-touch)` before touching anything else.** If it sits below
  45% with `n > 20`, the field is not describing this instrument and the
  honest move is to turn `zoiSeed` off and use v2 as a pivot tracker.
- **Trapped vs shelf.** On trending instruments raise `wTrapW`; trapped cohorts
  are created constantly and worked off slowly. On rotational instruments
  raise `wShelf` and `wVelW` — there is less directional stranding to find.
- **Burn rate is the knob for how long zones stay armed.** Too many stale ZOIs
  means `fuelBurn` is too low for your timeframe.
- **`binAtr` trades resolution for stability.** Below ~0.15 ATR the field gets
  noisy and peaks split; above ~0.35 it smears distinct shelves together.
