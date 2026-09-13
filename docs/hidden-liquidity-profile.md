# Hidden Liquidity Profile (HLP)

A Pine Script **v6** indicator that estimates where resting orders are hiding, built by
reasoning from what the order book necessarily leaves behind in OHLCV — not by
restyling a volume profile.

Source: [`indicators/hidden_liquidity_profile.pine`](../indicators/hidden_liquidity_profile.pine)

---

## The problem, stated honestly

Liquidity *is* resting orders. Resting orders live in the order book, and the book is
invisible on a chart — all we are given is `open`, `high`, `low`, `close`, `volume` per bar.

So the useful question is not *"how do I draw the book?"* (impossible) but:

> **What does a large resting order necessarily leave behind in OHLCV, that can be inverted
> back into evidence of its existence?**

Everything below follows from answering that.

---

## Derivation

### A1 — The mechanism

Price moves only when aggressive (market) orders exhaust the resting (limit) orders sitting
at a price. No exhaustion, no movement. This is not a heuristic; it is how a matching engine
works.

### A2 — The inversion (the core idea)

Invert A1. **Volume that did *not* move price is proof that something large and passive was
standing there absorbing it.** Displacement per unit of volume is therefore an *inverse*
measure of hidden size:

```
efficiency  e = |close − open| / (high − low)        ∈ [0, 1]
absorption  a = volume × (1 − e)^γ
```

This is the whole point of the indicator. A volume profile asks *"where did trade happen?"*
HLP asks *"where did trade happen **without result**?"* Those are different quantities, and
only the second one implies resting size.

The limiting case is correct by construction: a zero-range bar on heavy volume (`e = 0`)
scores maximum absorption — which is exactly what a wall in the book looks like from outside.

### A3 — Not all resting orders are limit orders

Stops cluster just beyond swing extremes, and their footprint is the *opposite* of
absorption: a fast penetration that immediately fails. A sweep — trade through a prior
extreme, close back inside it — marks a level that held a pool, and the volume spent taking
it bounds the pool's size.

### A4 — Negative evidence counts

Where price traversed a range with (almost) no trade — a gap / fair-value gap — there was
**no** liquidity. Such prices are penalised. Without this term the profile would mistake a
vacuum for a wall, since both can show up as "price did not linger here".

### A5 — The side is recoverable

After absorption, where the bar settles inside its own range says who won:

```
location l = (close − low) / (high − low)
bias     b = 2l − 1                                  ∈ [−1, +1]
```

Settling at the top means passive **bids** ate the selling (demand-side liquidity).
Settling at the bottom means passive **offers** ate the buying (supply-side liquidity).

### A6 — Evidence must be comparable across time

Raw volume drifts with session and regime, so it is divided by its own moving average before
use. A quiet hour and a busy hour then testify with equal weight.

### Composition

```
Score(p) = Σ absorption(p) + Σ stop-pool(p) − Σ void(p)
Skew(p)  = signed share of Score(p) attributable to demand vs supply
```

Each bar's absorption is smeared across every price it visited, in proportion to how much of
the bar's range each bin captured — so one bar contributes exactly its own weight, no more.

---

## Why this is not a volume profile

`γ = 0` collapses `(1 − e)^γ` to `1`, and the whole thing degenerates *exactly* into an
ordinary volume profile. That is the control case, and it is verified in the test suite.

The difference at `γ > 0` is not cosmetic. Constructed case:

| Price | Behaviour | Volume | Volume profile says | HLP says |
|-------|-----------|--------|---------------------|----------|
| 120 | every bar fully displaces (efficient churn) | 10,000 | **POC here** | nothing here |
| 100 | zero displacement, absorbed | 5,000 | minor node | **POL here** |

Twice the volume traded at 120, but all of it *moved price* — no one was defending it. Half
the volume traded at 100 and none of it moved price — someone was. A volume profile ranks
120 first; HLP ranks 100 first. **When the two disagree, the disagreement is the
information.**

---

## Reading it

| Element | Meaning |
|---------|---------|
| **Long bars** | Prices the market had to fight through. Magnets first, then barriers. Price decelerates into them. |
| **Short bars** | Prices that never held size. Price crosses them quickly — poor targets, poor stops. |
| **Green** | Absorption resolved upward → demand-side resting bids. |
| **Red** | Absorption resolved downward → supply-side resting offers. |
| **POL** | *Point of Liquidity* — the single most defended price in the window. Not the POC. |
| **Liquidity area** | The band containing `vaPct` of all evidence, expanded outward from the POL pair-by-pair. |
| **Shelves** | Local maxima projected forward as zones — the levels worth reacting to. |
| **Book skew** | Net demand vs supply share across the whole window. |

---

## Parameters

**Profile window** — `lookback` (bars used), `bins` (vertical resolution),
`volLen` (volume normaliser, A6).

**Model** — `γ` *absorption emphasis*: `0` = plain volume profile, `2` (default) = balanced,
`4–6` = keeps only the most stubborn, least-efficient volume. `swingLen` / `sweepW` control
stop pools (A3); `voidW` controls the gap penalty (A4). Each of the three terms can be
switched off independently, which makes their individual contribution easy to see.

**Display** — profile side/width/offset, liquidity-area %, shelf count, minimum shelf
strength, forward extension, colours, statistics table.

---

## Alerts

* `HLP: POL cross` — price crossed the Point of Liquidity.
* `HLP: shelf entry` — price entered the strongest hidden-liquidity shelf.

---

## Limitations — read these

* **Inference, not observation.** This estimates hidden liquidity from its footprint. It
  cannot see the book, and a footprint has more than one possible cause.
* **The profile is rebuilt only on the last bar.** That is a deliberate performance choice,
  but it means the levels are live values, not a historical series. They are suitable for
  real-time alerting and **not** for backtesting as-is.
* **Absorption and exhaustion look alike early.** A wall that holds and a wall that is about
  to break leave a similar footprint while the fight is ongoing; only the resolution
  separates them. Use the skew colour and what price does on the retest.
* **Volume quality bounds everything.** On instruments with synthetic or fragmented volume
  (many FX feeds), A2 is standing on sand. Tick volume is a weak substitute.
* **Low-volume gaps are ambiguous.** Overnight gaps and illiquid-session gaps both register
  as voids, though only one is structurally meaningful.

---

## Verification

The algorithm was ported to Python and checked against constructed cases: mass conservation
in the bar-to-bin smearing, correct localisation of absorption, the `γ = 0` degeneracy to a
volume profile, the discriminating case above, side detection in both directions, stop-pool
deposition and sign, void flagging, value-area termination and coverage, the
`|skew| ≤ total` invariant, and degenerate inputs (flat bars, zero volume, zero range).
